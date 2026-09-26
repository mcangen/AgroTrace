package co.agrofinca.passport;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface ProductPassportRepository extends JpaRepository<ProductPassport, Long> {

    Optional<ProductPassport> findByProductId(String productId);

    Optional<ProductPassport> findByPublicId(String publicId);
}
