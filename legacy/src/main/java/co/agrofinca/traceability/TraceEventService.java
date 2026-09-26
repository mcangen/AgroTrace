package co.agrofinca.traceability;

import co.agrofinca.farm.FarmRepository;
import co.agrofinca.farm.Product;
import co.agrofinca.farm.ProductRepository;
import co.agrofinca.shared.crypto.HashChain;
import co.agrofinca.shared.events.TraceEventRecorded;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class TraceEventService {

    private final TraceEventRepository traceEventRepository;
    private final ProductRepository productRepository;
    private final FarmRepository farmRepository;
    private final ApplicationEventPublisher eventPublisher;

    public TraceEventService(TraceEventRepository traceEventRepository,
                             ProductRepository productRepository,
                             FarmRepository farmRepository,
                             ApplicationEventPublisher eventPublisher) {
        this.traceEventRepository = traceEventRepository;
        this.productRepository = productRepository;
        this.farmRepository = farmRepository;
        this.eventPublisher = eventPublisher;
    }

    @Transactional
    public TraceEvent record(String productId, String eventType, String payload) {
        String prevHash = traceEventRepository
                .findTopByProductIdOrderByTimestampDesc(productId)
                .map(TraceEvent::getChainHash)
                .orElse("GENESIS");

        TraceEvent event = new TraceEvent();
        event.setProductId(productId);
        event.setEventType(eventType);
        event.setPayload(payload);
        event.setPayloadHash(HashChain.hashPayloadOnly(payload));
        event.setPrevHash(prevHash);
        event.setChainHash(HashChain.hash(payload, prevHash));

        TraceEvent saved = traceEventRepository.saveAndFlush(event);

        Product product = productRepository.findById(productId).orElseThrow();
        var farm = farmRepository.findById(product.getFarmId()).orElseThrow();

        eventPublisher.publishEvent(new TraceEventRecorded(
                saved, farm.getName(), product.getName(), product.getPublicId()
        ));

        return saved;
    }
}
