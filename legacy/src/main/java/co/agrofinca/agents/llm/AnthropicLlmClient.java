package co.agrofinca.agents.llm;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Service;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.List;
import java.util.Map;

@Service
@Primary
public class AnthropicLlmClient implements LlmClient {

    private static final Logger log = LoggerFactory.getLogger(AnthropicLlmClient.class);

    @Value("${anthropic.api.key}")
    private String apiKey;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public String complete(String systemPrompt, String userPrompt) {
        try {
            if (apiKey == null || apiKey.isBlank() || "FALLBACK_MODE".equals(apiKey)) {
                log.warn("LLM in fallback mode — API key not configured");
                return null;
            }

            Map<String, Object> bodyMap = Map.of(
                    "model", "claude-haiku-4-5-20251001",
                    "max_tokens", 800,
                    "system", systemPrompt,
                    "messages", List.of(Map.of("role", "user", "content", userPrompt))
            );
            String requestBody = objectMapper.writeValueAsString(bodyMap);

            HttpClient client = HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(10))
                    .build();

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create("https://api.anthropic.com/v1/messages"))
                    .header("Content-Type", "application/json")
                    .header("x-api-key", apiKey)
                    .header("anthropic-version", "2023-06-01")
                    .POST(HttpRequest.BodyPublishers.ofString(requestBody))
                    .timeout(Duration.ofSeconds(20))
                    .build();

            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() != 200) {
                log.error("Anthropic API error: {} {}", response.statusCode(), response.body());
                return null;
            }

            JsonNode root = objectMapper.readTree(response.body());
            return root.path("content").get(0).path("text").asText();

        } catch (Exception e) {
            log.error("AnthropicLlmClient error: {}", e.getMessage());
            return null;
        }
    }
}
