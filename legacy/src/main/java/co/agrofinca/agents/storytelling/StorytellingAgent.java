package co.agrofinca.agents.storytelling;

import co.agrofinca.agents.llm.FallbackContent;
import co.agrofinca.agents.llm.LlmClient;
import co.agrofinca.passport.PassportService;
import co.agrofinca.shared.events.TraceEventRecorded;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;

@Component
public class StorytellingAgent {

    private static final Logger log = LoggerFactory.getLogger(StorytellingAgent.class);

    private final LlmClient llmClient;
    private final PassportService passportService;

    public StorytellingAgent(LlmClient llmClient, PassportService passportService) {
        this.llmClient = llmClient;
        this.passportService = passportService;
    }

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    @Async
    public void onTraceEvent(TraceEventRecorded event) {
        String systemPrompt =
                "Eres un agente de storytelling especializado en productos " +
                "agroturísticos colombianos. Tu misión es escribir historias " +
                "auténticas, evocadoras y breves que conecten emocionalmente " +
                "al comprador internacional con el origen del producto. " +
                "Escribe exactamente 3 oraciones. No incluyas títulos, " +
                "encabezados ni explicaciones. Solo la historia.";

        String userPrompt =
                "Producto: " + event.productName() + "\n" +
                "Finca: " + event.farmName() + "\n" +
                "Evento registrado: " + event.traceEvent().getEventType() + "\n" +
                "Datos del evento: " + event.traceEvent().getPayload() + "\n" +
                "Escribe la historia de origen de este producto.";

        String result = llmClient.complete(systemPrompt, userPrompt);

        if (result == null || result.isBlank()) {
            result = FallbackContent.STORY_ES;
            log.warn("StorytellingAgent using fallback for product: {}",
                    event.traceEvent().getProductId());
        }

        String productId = event.traceEvent().getProductId();
        passportService.updateStory(productId, result.trim());
        log.info("Story saved for product: {} | preview: {}...",
                productId,
                result.substring(0, Math.min(60, result.length())));
    }
}
