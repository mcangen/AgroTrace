package co.agrofinca.agents.llm;

public interface LlmClient {

    String complete(String systemPrompt, String userPrompt);
}
