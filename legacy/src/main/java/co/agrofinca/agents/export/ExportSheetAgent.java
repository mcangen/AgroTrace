package co.agrofinca.agents.export;

import co.agrofinca.agents.llm.FallbackContent;
import co.agrofinca.agents.llm.LlmClient;
import co.agrofinca.passport.PassportService;
import co.agrofinca.shared.events.TraceEventRecorded;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;

@Component
public class ExportSheetAgent {

    private static final Logger log = LoggerFactory.getLogger(ExportSheetAgent.class);

    private final LlmClient llmClient;
    private final PassportService passportService;
    private final ObjectMapper objectMapper;

    public ExportSheetAgent(LlmClient llmClient,
                            PassportService passportService,
                            ObjectMapper objectMapper) {
        this.llmClient = llmClient;
        this.passportService = passportService;
        this.objectMapper = objectMapper;
    }

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    @Async
    public void onTraceEvent(TraceEventRecorded event) {
        String systemPrompt =
                "You are an export documentation agent for Colombian agricultural " +
                "products. Generate a structured product sheet for international " +
                "buyers. You MUST respond with a valid JSON object only. " +
                "No markdown, no backticks, no explanation before or after. " +
                "The JSON must have exactly these four fields:\n" +
                "{\n" +
                "  \"titleEs\": \"short product title in Spanish\",\n" +
                "  \"titleEn\": \"short product title in English\",\n" +
                "  \"bodyEs\": \"2-sentence product description in Spanish\",\n" +
                "  \"bodyEn\": \"2-sentence product description in English\"\n" +
                "}";

        String userPrompt =
                "Product: " + event.productName() + "\n" +
                "Farm: " + event.farmName() + ", Colombia\n" +
                "Event: " + event.traceEvent().getEventType() + "\n" +
                "Data: " + event.traceEvent().getPayload() + "\n" +
                "Generate the export sheet JSON.";

        String productId = event.traceEvent().getProductId();
        String result = llmClient.complete(systemPrompt, userPrompt);

        if (result == null) {
            applyFallback(productId);
            return;
        }

        try {
            String cleaned = result.strip();
            if (cleaned.startsWith("```")) {
                int firstNewline = cleaned.indexOf('\n');
                int lastFence = cleaned.lastIndexOf("```");
                cleaned = cleaned.substring(firstNewline + 1, lastFence).strip();
            }

            JsonNode node = objectMapper.readTree(cleaned);
            String titleEs = node.path("titleEs").asText(null);
            String titleEn = node.path("titleEn").asText(null);
            String bodyEs  = node.path("bodyEs").asText(null);
            String bodyEn  = node.path("bodyEn").asText(null);

            if (isBlankOrNull(titleEs) || isBlankOrNull(titleEn)
                    || isBlankOrNull(bodyEs) || isBlankOrNull(bodyEn)) {
                applyFallback(productId);
                return;
            }

            passportService.updateExportSheet(productId, titleEs, titleEn, bodyEs, bodyEn);
            log.info("Export sheet saved for product: {}", productId);

        } catch (Exception e) {
            log.warn("ExportSheetAgent JSON parse failed, using fallback: {}", e.getMessage());
            applyFallback(productId);
        }
    }

    private void applyFallback(String productId) {
        passportService.updateExportSheet(
                productId,
                FallbackContent.EXPORT_TITLE_ES,
                FallbackContent.EXPORT_TITLE_EN,
                FallbackContent.EXPORT_BODY_ES,
                FallbackContent.EXPORT_BODY_EN
        );
        log.warn("ExportSheetAgent using fallback for product: {}", productId);
    }

    private boolean isBlankOrNull(String s) {
        return s == null || s.isBlank();
    }
}
