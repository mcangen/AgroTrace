package co.agrofinca.farm;

import co.agrofinca.traceability.TraceEventService;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@Component
public class FarmDataSeeder implements CommandLineRunner {

    private final FarmRepository farmRepository;
    private final ProductRepository productRepository;
    private final TraceEventService traceEventService;

    public FarmDataSeeder(FarmRepository farmRepository,
                          ProductRepository productRepository,
                          TraceEventService traceEventService) {
        this.farmRepository = farmRepository;
        this.productRepository = productRepository;
        this.traceEventService = traceEventService;
    }

    @Override
    public void run(String... args) throws Exception {
        if (farmRepository.count() != 0) {
            return;
        }

        farmRepository.save(new Farm(
                "farm-001",
                "Finca La Esperanza",
                "Sierra Nevada, Magdalena, Colombia",
                "Familia Pérez"
        ));

        productRepository.save(new Product(
                "prod-001",
                "farm-001",
                "Cacao fino de aroma",
                "Cultivado a 600m sobre el nivel del mar, secado al sol por seis días",
                "la-esperanza-cacao-001"
        ));

        traceEventService.record(
                "prod-001",
                "PLANTING",
                "{\"date\":\"2025-03-12\",\"area_m2\":2000,\"variety\":\"CCN-51\",\"altitude_m\":600}"
        );

        Thread.sleep(100);

        traceEventService.record(
                "prod-001",
                "HARVEST",
                "{\"date\":\"2026-05-28\",\"kg\":320,\"quality\":\"Grade A\",\"harvested_by\":\"Familia Pérez\"}"
        );

        Thread.sleep(100);

        traceEventService.record(
                "prod-001",
                "DRYING",
                "{\"date\":\"2026-06-03\",\"days\":6,\"method\":\"sun-dried\",\"humidity_pct\":7}"
        );
    }
}
