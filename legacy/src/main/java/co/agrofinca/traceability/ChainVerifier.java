package co.agrofinca.traceability;

import co.agrofinca.shared.crypto.HashChain;
import org.springframework.stereotype.Component;
import java.util.List;

@Component
public class ChainVerifier {

    private final TraceEventRepository traceEventRepository;

    public ChainVerifier(TraceEventRepository traceEventRepository) {
        this.traceEventRepository = traceEventRepository;
    }

    public VerificationResult verify(String productId) {
        List<TraceEvent> events = traceEventRepository.findByProductIdOrderByTimestampAsc(productId);

        if (events.size() <= 1) {
            return VerificationResult.clean();
        }

        for (int i = 1; i < events.size(); i++) {
            TraceEvent current = events.get(i);
            TraceEvent previous = events.get(i - 1);
            String expected = HashChain.hash(current.getPayload(), previous.getChainHash());
            if (!expected.equals(current.getChainHash())) {
                return new VerificationResult(false, i, current.getId());
            }
        }

        return VerificationResult.clean();
    }
}
