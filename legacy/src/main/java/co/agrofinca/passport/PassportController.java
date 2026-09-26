package co.agrofinca.passport;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/passport")
@CrossOrigin(origins = "*")
public class PassportController {

    private final ProductPassportRepository passportRepository;

    public PassportController(ProductPassportRepository passportRepository) {
        this.passportRepository = passportRepository;
    }

    @GetMapping("/public/{publicId}")
    public ResponseEntity<ProductPassport> getByPublicId(@PathVariable String publicId) {
        return passportRepository.findByPublicId(publicId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/product/{productId}")
    public ResponseEntity<ProductPassport> getByProductId(@PathVariable String productId) {
        return passportRepository.findByProductId(productId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}
