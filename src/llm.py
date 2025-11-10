import json
from rdflib import Graph
from openai import AzureOpenAI
from typing import List, Dict, Any, Tuple

class MTGQuerySystemAzure:
    def __init__(self, ttl_file_path, azure_config: Dict, max_retries=3):
        """
        azure_config should contain:
        - endpoint: your Azure OpenAI endpoint
        - api_key: your API key
        - deployment: your model deployment name (e.g., 'gpt-4-turbo')
        - api_version: API version (e.g., '2024-02-15-preview')
        """
        # Load RDF database
        self.graph = Graph()
        self.graph.parse(ttl_file_path, format="turtle")
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=azure_config['endpoint'],
            api_key=azure_config['api_key'],
            api_version=azure_config.get('api_version', '2024-02-15-preview')
        )
        self.deployment = azure_config['deployment']
        self.max_retries = max_retries
        
        # Extract schema for context
        self.schema = self.extract_schema()
    
    def extract_schema(self):
        """Extract schema information to help LLM understand the data"""
        # Get predicates
        pred_query = """
        SELECT DISTINCT ?predicate WHERE {
            ?s ?predicate ?o
        } LIMIT 100
        """
        predicates = [str(row[0]) for row in self.graph.query(pred_query)]
        
        # Get sample data
        sample_query = """
        SELECT ?card ?name WHERE {
            ?card :name ?name .
            FILTER(CONTAINS(LCASE(?name), "counterspell"))
        } LIMIT 5
        """
        samples = list(self.graph.query(sample_query))
        
        return {
            "predicates": predicates,
            "sample_cards": [str(row[1]) for row in samples] if samples else []
        }
    
    def execute_sparql(self, query: str) -> Dict[str, Any]:
        """Execute SPARQL query and return results"""
        try:
            results = self.graph.query(query)
            result_list = [
                {str(var): str(row[var]) for var in results.vars}
                for row in results
            ]
            
            return {
                "success": True,
                "count": len(result_list),
                "results": result_list,
                "query": query
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": []
            }
    
    def validate_answer(self, question: str, query: str, results: Dict, answer: str) -> Tuple[bool, str]:
        """Validate if the answer actually addresses the question"""
        
        validation_messages = [
            {
                "role": "system",
                "content": "You are a validation assistant that checks if answers properly address questions."
            },
            {
                "role": "user",
                "content": f"""
                Original Question: {question}
                
                SPARQL Query Executed: {query}
                
                Results Retrieved: {json.dumps(results['results'][:10], indent=2)}
                Result Count: {results['count']}
                
                Generated Answer: {answer}
                
                Evaluate whether this answer satisfactorily addresses the original question.
                
                Consider:
                1. Does the answer directly address what was asked?
                2. If asking for a count, does the answer provide a specific number?
                3. If asking for names/items, does the answer list them?
                4. Is the answer based on the actual results or is it evasive?
                
                Respond with JSON only:
                {{
                    "satisfactory": true or false,
                    "reason": "explanation",
                    "missing": "what specific information is missing",
                    "suggestion": "how to improve the query"
                }}
                """
            }
        ]
        
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=validation_messages,
            temperature=0,
            response_format={"type": "json_object"}  # Azure OpenAI JSON mode
        )
        
        try:
            validation = json.loads(response.choices[0].message.content)
            return validation["satisfactory"], validation
        except:
            return True, {"reason": "Could not validate"}
    
    def query_with_retry(self, natural_language_question: str):
        """Main query method with retry logic"""
        conversation_history = []
        all_attempts = []
        
        for attempt in range(self.max_retries):
            print(f"\n--- Attempt {attempt + 1} ---")
            
            # Build context from previous attempts
            context = self._build_context(
                natural_language_question, 
                all_attempts
            )
            
            # Generate and execute SPARQL
            result = self._single_attempt(
                context, 
                conversation_history,
                natural_language_question
            )
            
            all_attempts.append(result)
            
            # Check if we got meaningful results
            if result["execution"]["success"] and result["execution"]["count"] > 0:
                # Generate answer
                answer = self._generate_final_answer(
                    natural_language_question,
                    result["execution"],
                    result["sparql"]
                )
                
                # Validate the answer
                is_satisfactory, validation_details = self.validate_answer(
                    natural_language_question,
                    result["sparql"],
                    result["execution"],
                    answer
                )
                
                result["answer"] = answer
                result["validation"] = validation_details
                
                if is_satisfactory:
                    print(f"✓ Answer validated as satisfactory")
                    return {
                        "success": True,
                        "answer": answer,
                        "attempts": attempt + 1,
                        "final_query": result["sparql"],
                        "results": result["execution"]["results"]
                    }
                else:
                    print(f"✗ Answer not satisfactory: {validation_details['reason']}")
                    if attempt < self.max_retries - 1:
                        conversation_history = self._prepare_retry_with_feedback(
                            result, 
                            validation_details,
                            conversation_history
                        )
            else:
                print("✗ Query returned no results or failed")
                if attempt < self.max_retries - 1:
                    conversation_history = self._prepare_retry_context(
                        result, 
                        conversation_history
                    )
        
        # All attempts failed
        return {
            "success": False,
            "answer": "Unable to find satisfactory results after multiple attempts.",
            "attempts": self.max_retries,
            "all_attempts": all_attempts
        }
    
    def _single_attempt(self, context: str, history: List[Dict], question: str) -> Dict:
        """Execute a single attempt using Azure OpenAI function calling"""
        
        # Define the function for OpenAI
        functions = [
            {
                "name": "execute_sparql",
                "description": "Execute a SPARQL query against the MTG RDF database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SPARQL query to execute"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Explanation of what this query is trying to find"
                        }
                    },
                    "required": ["query", "reasoning"]
                }
            }
        ]
        
        messages = [
            {
                "role": "system",
                "content": f"""You are a SPARQL query expert for an MTG card database.
                
                Database schema:
                Predicates: {', '.join(self.schema['predicates'][:30])}
                Sample cards: {', '.join(self.schema['sample_cards'])}
                
                When searching for "versions" of a card, look for:
                - Different sets/editions (using :set, :setCode, :printings predicates)
                - Each unique combination of card + set is a different version
                - Use GROUP BY and COUNT for aggregations
                """
            }
        ]
        
        # Add conversation history
        messages.extend(history)
        
        # Add current context
        messages.append({
            "role": "user",
            "content": f"{context}\n\nQuestion to answer: {question}"
        })
        
        # Call Azure OpenAI with function calling
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            functions=functions,
            function_call="auto",  # Let the model decide when to call the function
            temperature=0
        )
        
        # Check if function was called
        message = response.choices[0].message
        
        if message.function_call:
            # Extract function arguments
            function_args = json.loads(message.function_call.arguments)
            sparql_query = function_args.get("query")
            reasoning = function_args.get("reasoning", "")
            
            print(f"Generated SPARQL:\n{sparql_query}")
            print(f"Reasoning: {reasoning}")
            
            # Execute the query
            execution_result = self.execute_sparql(sparql_query)
            print(f"Results: {execution_result['count']} rows")
            
            return {
                "sparql": sparql_query,
                "reasoning": reasoning,
                "execution": execution_result
            }
        
        return {
            "sparql": None,
            "reasoning": "No query generated",
            "execution": {"success": False, "count": 0, "results": []}
        }
    
    def _build_context(self, question: str, previous_attempts: List[Dict]) -> str:
        """Build context including previous failed attempts"""
        context = f"User question: {question}"
        
        if previous_attempts:
            context += "\n\nPrevious attempts that didn't work:"
            for i, attempt in enumerate(previous_attempts):
                context += f"\n\nAttempt {i+1}:"
                context += f"\nQuery: {attempt.get('sparql', 'N/A')}"
                
                if 'validation' in attempt and not attempt['validation'].get('satisfactory', True):
                    context += f"\nIssue: {attempt['validation']['reason']}"
                    context += f"\nSuggestion: {attempt['validation'].get('suggestion', 'N/A')}"
                elif attempt['execution']['count'] == 0:
                    context += "\nIssue: Returned no results"
                elif not attempt['execution']['success']:
                    context += f"\nError: {attempt['execution'].get('error', 'Unknown')}"
            
            context += "\n\nPlease try a different approach. Consider:"
            context += "\n- Check spelling and case sensitivity"
            context += "\n- Use FILTER with CONTAINS for partial matches"
            context += "\n- Try different predicates"
            context += "\n- Use OPTIONAL for properties that might not exist"
        
        return context
    
    def _prepare_retry_context(self, last_result: Dict, history: List[Dict]) -> List[Dict]:
        """Prepare conversation for retry after failure"""
        new_history = history.copy()
        
        new_history.append({
            "role": "assistant",
            "content": f"I tried this query but got no results: {last_result.get('sparql', 'No query generated')}"
        })
        
        new_history.append({
            "role": "user",
            "content": "The query returned no results. Please try a different approach using partial matching, case-insensitive search, or broader criteria."
        })
        
        return new_history
    
    def _prepare_retry_with_feedback(self, last_result: Dict, validation: Dict, history: List[Dict]) -> List[Dict]:
        """Prepare retry with validation feedback"""
        new_history = history.copy()
        
        new_history.append({
            "role": "assistant",
            "content": f"My query returned {last_result['execution']['count']} results but didn't fully answer the question."
        })
        
        new_history.append({
            "role": "user",
            "content": f"""The answer wasn't satisfactory. 
            Issue: {validation['reason']}
            Missing: {validation.get('missing', 'Not specified')}
            Suggestion: {validation.get('suggestion', 'Try a different approach')}
            
            Please generate a new query that addresses these issues."""
        })
        
        return new_history
    
    def _generate_final_answer(self, question: str, execution_result: Dict, sparql_query: str) -> str:
        """Generate natural language answer from results"""
        
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that provides clear, concise answers based on query results."
            },
            {
                "role": "user",
                "content": f"""Original question: {question}
                
                SPARQL query executed:
                {sparql_query}
                
                Query results:
                {json.dumps(execution_result['results'][:20], indent=2)}
                
                Total results: {execution_result['count']}
                
                Please provide a clear, natural language answer to the original question based on these results.
                Be specific with numbers and details from the results."""
            }
        ]
        
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=0,
            max_tokens=500
        )
        
        return response.choices[0].message.content

# Usage Example
if __name__ == "__main__":
    # Configure Azure OpenAI
    azure_config = {
        "endpoint": "https://your-resource.openai.azure.com/",
        "api_key": "your-api-key-here",
        "deployment": "gpt-4-turbo",  # or "gpt-35-turbo", etc.
        "api_version": "2024-02-15-preview"
    }
    
    # Initialize system
    mtg_system = MTGQuerySystemAzure(
        ttl_file_path="mtg_cards.ttl",
        azure_config=azure_config,
        max_retries=3
    )
    
    # Query the system
    result = mtg_system.query_with_retry("How many versions of counterspell exist?")
    
    if result["success"]:
        print(f"\n✓ Final Answer: {result['answer']}")
        print(f"Found answer in {result['attempts']} attempt(s)")
        print(f"Query used: {result['final_query']}")
    else:
        print(f"\n✗ Failed: {result['answer']}")
