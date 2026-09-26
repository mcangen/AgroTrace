package co.agrofinca.passport;

import co.agrofinca.farm.FarmRepository;
import co.agrofinca.farm.ProductRepository;
import co.agrofinca.shared.events.TraceEventRecorded;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;

@Component
public class PassportEventListener {

    private final PassportService passportService;
    private final ProductRepository productRepository;
    private final FarmRepository farmRepository;

    public PassportEventListener(PassportService passportService,
                                 ProductRepository productRepository,
                                 FarmRepository farmRepository) {
        this.passportService = passportService;
        this.productRepository = productRepository;
        this.farmRepository = farmRepository;
    }

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    @Async
    public void onTraceEventRecorded(TraceEventRecorded event) {
        String productId = event.traceEvent().getProductId();

        String location = productRepository.findById(productId)
                .flatMap(product -> farmRepository.findById(product.getFarmId()))
                .map(farm -> farm.getLocation())
                .orElse(null);

        passportService.getOrCreate(
                productId,
                event.productPublicId(),
                event.farmName(),
                event.productName(),
                location
        );

        passportService.updateReputation(productId);
    }
}
