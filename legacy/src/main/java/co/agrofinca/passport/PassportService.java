package co.agrofinca.passport;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PassportService {

    private final ProductPassportRepository passportRepository;

    public PassportService(ProductPassportRepository passportRepository) {
        this.passportRepository = passportRepository;
    }

    @Transactional
    public ProductPassport getOrCreate(String productId, String publicId,
                                       String farmName, String productName,
                                       String location) {
        return passportRepository.findByProductId(productId)
                .orElseGet(() -> {
                    ProductPassport p = new ProductPassport();
                    p.setProductId(productId);
                    p.setPublicId(publicId);
                    p.setFarmName(farmName);
                    p.setProductName(productName);
                    p.setProductLocation(location);
                    p.setReputationScore(4.0);
                    return passportRepository.save(p);
                });
    }

    @Transactional
    public ProductPassport updateReputation(String productId) {
        return passportRepository.findByProductId(productId)
                .map(passport -> {
                    double raw = Math.min(5.0, passport.getReputationScore() + 0.1);
                    double rounded = Math.round(raw * 10.0) / 10.0;
                    passport.setReputationScore(rounded);
                    return passportRepository.save(passport);
                })
                .orElse(null);
    }

    @Transactional
    public ProductPassport updateStory(String productId, String story) {
        return passportRepository.findByProductId(productId)
                .map(passport -> {
                    passport.setStoryEs(story);
                    return passportRepository.save(passport);
                })
                .orElse(null);
    }

    @Transactional
    public ProductPassport updateExportSheet(String productId, String titleEs,
                                             String titleEn, String bodyEs,
                                             String bodyEn) {
        return passportRepository.findByProductId(productId)
                .map(passport -> {
                    passport.setExportTitleEs(titleEs);
                    passport.setExportTitleEn(titleEn);
                    passport.setExportBodyEs(bodyEs);
                    passport.setExportBodyEn(bodyEn);
                    return passportRepository.save(passport);
                })
                .orElse(null);
    }
}
