# Persistence
[Symbol Layier@LangChain Docs: LangGraph@https://docs.langchain.com/oss/python/langgraph/persistence]
"Persistence lets LangGraph applications keep useful information beyond a single graph run. It matters when an agent needs to continue a conversation, resume after an interruption, recover from a failure, or remember information across interactions."

## Scenario
1. [nltk_data:framenet_v17@Remembering_information]"Persistence lets LangGraph applications keep useful information beyond a single graph run."
   The Scenario states "Cognizer saved the Mental_content in Memory, and can retrieve it. The Mental_content can be Explicit Proposition，Embedded  Question or [Noun Phrase]Hidden Question(via *the price* ≈ what is the price)" -> [Schemata@Persistence:Debug]:
   `[Generate]` 1.Explicit Proposition/ 2.Embedded Question/ 3.Hidden Question ->
   `[Save]` 1.Memory/2.DB ->
   `[Retrieve Keyword]` 1.Keyword can be computing

2. [nltk_data:framenet_v17@Activity_resume]"...resume after an interruption, recover from a failure..."
    The Scenario states "The Agent resumes the Activity state to normal, and the progress is saved before the interruption" -> Trigger[Fallback:Release].This Scenario appends an optional `[After State]` 1.Normal /2.Interruption /3.Failure /4.Termination

## Assertions
Persistence is a pre_condition for Continue a conversation、Resume after interrupt(Interruption, Failure)、Across scope conversation(via Long Conversation).

But, 
1. what affecting could be if Mental_content is Explicit Proposition, Embedded Question, or Hidden Question ?

## Runtime Instances

### Continue a conversation
```python

```
1. from langchain.chat_models import init_chat_model vs from langchain_openai import ChatOpenAI