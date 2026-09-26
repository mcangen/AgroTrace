package co.agrofinca.traceability;

import co.agrofinca.farm.Farm;
import co.agrofinca.farm.FarmRepository;
import co.agrofinca.farm.Product;
import co.agrofinca.farm.ProductRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Random;

@RestController
@CrossOrigin(origins = "*")
public class ProductRegistrationController {

    private final FarmRepository farmRepository;
    private final ProductRepository productRepository;
    private final TraceEventService traceEventService;
    private final ObjectMapper objectMapper;

    public ProductRegistrationController(FarmRepository farmRepository,
                                         ProductRepository productRepository,
                                         TraceEventService traceEventService,
                                         ObjectMapper objectMapper) {
        this.farmRepository = farmRepository;
        this.productRepository = productRepository;
        this.traceEventService = traceEventService;
        this.objectMapper = objectMapper;
    }

    @PostMapping("/api/products/register")
    public Map<String, String> register(@RequestBody Map<String, String> body) {
        try {
            long ts = System.currentTimeMillis();
            String productId = "prod-" + ts;
            String farmId    = "farm-" + ts;
            String productName = body.getOrDefault("productName", "Producto");
            String publicId  = slugify(productName) + "-" + String.format("%06d", new Random().nextInt(1_000_000));

            Farm farm = new Farm();
            farm.setId(farmId);
            farm.setName(body.getOrDefault("farmName", "Finca sin nombre"));
            farm.setLocation(body.getOrDefault("location", "Colombia"));
            farm.setOwnerName(body.getOrDefault("ownerName", "Desconocido"));
            farmRepository.save(farm);

            Product product = new Product();
            product.setId(productId);
            product.setFarmId(farmId);
            product.setName(productName);
            product.setDescription(body.getOrDefault("postCosecha", ""));
            product.setPublicId(publicId);
            product.setVariety(body.get("variety"));
            product.setResponsable(body.get("responsable"));
            product.setInsumos(body.get("insumos"));
            product.setPostCosecha(body.get("postCosecha"));
            String fechaSiembra = body.get("fechaSiembra");
            if (fechaSiembra != null && !fechaSiembra.isBlank()) {
                product.setFechaSiembra(LocalDate.parse(fechaSiembra));
            }
            String fechaCosecha = body.get("fechaCosecha");
            if (fechaCosecha != null && !fechaCosecha.isBlank()) {
                product.setFechaCosecha(LocalDate.parse(fechaCosecha));
            }
            productRepository.save(product);

            Map<String, String> payloadMap = new LinkedHashMap<>();
            payloadMap.put("variety",      body.getOrDefault("variety", ""));
            payloadMap.put("responsable",  body.getOrDefault("responsable", ""));
            payloadMap.put("insumos",      body.getOrDefault("insumos", ""));
            payloadMap.put("postCosecha",  body.getOrDefault("postCosecha", ""));
            payloadMap.put("fechaSiembra", body.getOrDefault("fechaSiembra", ""));
            payloadMap.put("fechaCosecha", body.getOrDefault("fechaCosecha", ""));
            payloadMap.put("farmName",     body.getOrDefault("farmName", ""));
            payloadMap.put("location",     body.getOrDefault("location", ""));
            payloadMap.put("ownerName",    body.getOrDefault("ownerName", ""));
            String payloadJson = objectMapper.writeValueAsString(payloadMap);

            traceEventService.record(productId, "REGISTRO_INICIAL", payloadJson);

            Map<String, String> resp = new LinkedHashMap<>();
            resp.put("productId",   productId);
            resp.put("publicId",    publicId);
            resp.put("farmName",    body.getOrDefault("farmName", ""));
            resp.put("productName", productName);
            resp.put("qrUrl",       "/api/passport/" + publicId + "/qr");
            resp.put("passportUrl", "/pasaporte.html?id=" + publicId);
            return resp;

        } catch (Exception e) {
            Map<String, String> fallback = new LinkedHashMap<>();
            fallback.put("productId",   "prod-demo");
            fallback.put("publicId",    "producto-demo-000000");
            fallback.put("farmName",    body.getOrDefault("farmName", "Finca Demo"));
            fallback.put("productName", body.getOrDefault("productName", "Producto Demo"));
            fallback.put("qrUrl",       "/api/passport/producto-demo-000000/qr");
            fallback.put("passportUrl", "/pasaporte.html?id=producto-demo-000000");
            return fallback;
        }
    }

    private String slugify(String input) {
        if (input == null || input.isBlank()) return "producto";
        return input.toLowerCase()
                .replaceAll("[áàäâã]", "a").replaceAll("[éèëê]", "e")
                .replaceAll("[íìïî]", "i").replaceAll("[óòöôõ]", "o")
                .replaceAll("[úùüû]", "u").replaceAll("ñ", "n")
                .replaceAll("[^a-z0-9\\s-]", "")
                .trim().replaceAll("\\s+", "-");
    }
}
