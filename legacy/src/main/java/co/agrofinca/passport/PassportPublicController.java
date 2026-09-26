package co.agrofinca.passport;

import co.agrofinca.traceability.ChainVerifier;
import co.agrofinca.traceability.TraceEvent;
import co.agrofinca.traceability.TraceEventRepository;
import com.google.zxing.BarcodeFormat;
import com.google.zxing.client.j2se.MatrixToImageWriter;
import com.google.zxing.common.BitMatrix;
import com.google.zxing.qrcode.QRCodeWriter;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import java.io.ByteArrayOutputStream;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/passport")
@CrossOrigin(origins = "*")
public class PassportPublicController {

    private final ProductPassportRepository passportRepository;
    private final TraceEventRepository traceEventRepository;
    private final ChainVerifier chainVerifier;

    public PassportPublicController(ProductPassportRepository passportRepository,
                                    TraceEventRepository traceEventRepository,
                                    ChainVerifier chainVerifier) {
        this.passportRepository = passportRepository;
        this.traceEventRepository = traceEventRepository;
        this.chainVerifier = chainVerifier;
    }

    @GetMapping("/{publicId}")
    public ResponseEntity<Map<String, Object>> getPassport(@PathVariable String publicId) {
        return passportRepository.findByPublicId(publicId)
                .map(passport -> {
                    String productId = passport.getProductId();
                    List<TraceEvent> events = traceEventRepository
                            .findByProductIdOrderByTimestampAsc(productId);
                    boolean verified = chainVerifier.verify(productId).ok();

                    Map<String, Object> resp = new LinkedHashMap<>();
                    resp.put("productId",       productId);
                    resp.put("publicId",         passport.getPublicId());
                    resp.put("productName",      passport.getProductName());
                    resp.put("farmName",         passport.getFarmName());
                    resp.put("productLocation",  passport.getProductLocation());
                    resp.put("storyEs",          passport.getStoryEs());
                    resp.put("exportTitleEs",    passport.getExportTitleEs());
                    resp.put("exportTitleEn",    passport.getExportTitleEn());
                    resp.put("exportBodyEs",     passport.getExportBodyEs());
                    resp.put("exportBodyEn",     passport.getExportBodyEn());
                    resp.put("reputationScore",  passport.getReputationScore());
                    resp.put("lastUpdated",      passport.getLastUpdated());
                    resp.put("verified",         verified);
                    resp.put("timeline", events.stream().map(e -> {
                        Map<String, Object> m = new LinkedHashMap<>();
                        m.put("id",        e.getId());
                        m.put("eventType", e.getEventType());
                        m.put("payload",   e.getPayload());
                        m.put("chainHash", e.getChainHash());
                        m.put("prevHash",  e.getPrevHash());
                        m.put("timestamp", e.getTimestamp());
                        return m;
                    }).toList());

                    return ResponseEntity.ok(resp);
                })
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/{publicId}/qr")
    public ResponseEntity<byte[]> getQr(@PathVariable String publicId,
                                        HttpServletRequest request) {
        try {
            String scheme = request.getScheme();
            String host   = request.getServerName();
            int    port   = request.getServerPort();
            String baseUrl = scheme + "://" + host +
                    (( "http".equals(scheme) && port == 80) ||
                     ("https".equals(scheme) && port == 443) ? "" : ":" + port);

            String url = baseUrl + "/pasaporte.html?id=" + publicId;

            QRCodeWriter writer = new QRCodeWriter();
            BitMatrix matrix = writer.encode(url, BarcodeFormat.QR_CODE, 260, 260);

            ByteArrayOutputStream out = new ByteArrayOutputStream();
            MatrixToImageWriter.writeToStream(matrix, "PNG", out);

            return ResponseEntity.ok()
                    .contentType(MediaType.IMAGE_PNG)
                    .body(out.toByteArray());
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
}
