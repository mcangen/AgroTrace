package co.agrofinca.traceability;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class TraceController {

    private final TraceEventService traceEventService;
    private final ChainVerifier chainVerifier;
    private final TraceEventRepository traceEventRepository;

    public TraceController(TraceEventService traceEventService,
                           ChainVerifier chainVerifier,
                           TraceEventRepository traceEventRepository) {
        this.traceEventService = traceEventService;
        this.chainVerifier = chainVerifier;
        this.traceEventRepository = traceEventRepository;
    }

    @PostMapping("/products/{productId}/events")
    public Map<String, Object> recordEvent(@PathVariable String productId,
                                           @RequestBody Map<String, String> body) {
        String eventType = body.get("eventType");
        String payload = body.get("payload");
        TraceEvent saved = traceEventService.record(productId, eventType, payload);

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("eventId", saved.getId());
        response.put("productId", saved.getProductId());
        response.put("eventType", saved.getEventType());
        response.put("chainHash", saved.getChainHash());
        response.put("timestamp", saved.getTimestamp());
        response.put("verificationStatus", "SEALED");
        return response;
    }

    @GetMapping("/products/{productId}/chain")
    public List<Map<String, Object>> getChain(@PathVariable String productId) {
        return traceEventRepository
                .findByProductIdOrderByTimestampAsc(productId)
                .stream()
                .map(e -> {
                    Map<String, Object> m = new LinkedHashMap<>();
                    m.put("id", e.getId());
                    m.put("eventType", e.getEventType());
                    m.put("payload", e.getPayload());
                    m.put("chainHash", e.getChainHash());
                    m.put("prevHash", e.getPrevHash());
                    m.put("timestamp", e.getTimestamp());
                    return m;
                })
                .toList();
    }

    @GetMapping("/products/{productId}/verify")
    public VerificationResult verify(@PathVariable String productId) {
        return chainVerifier.verify(productId);
    }

    @PostMapping("/demo/tamper/{eventId}")
    public ResponseEntity<Map<String, String>> tamper(@PathVariable Long eventId,
                                                      @RequestBody Map<String, String> body) {
        return traceEventRepository.findById(eventId)
                .map(event -> {
                    event.setPayload(body.get("newPayload"));
                    traceEventRepository.save(event);
                    Map<String, String> response = new LinkedHashMap<>();
                    response.put("message", "Chain compromised at event #" + eventId);
                    response.put("warning", "DEMO ONLY — not a production endpoint");
                    return ResponseEntity.ok(response);
                })
                .orElse(ResponseEntity.notFound().<Map<String, String>>build());
    }
}
