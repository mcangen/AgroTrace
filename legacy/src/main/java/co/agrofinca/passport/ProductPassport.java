package co.agrofinca.passport;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "product_passports")
public class ProductPassport {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String productId;

    @Column(nullable = false, unique = true)
    private String publicId;

    private String farmName;
    private String productName;
    private String productLocation;

    @Column(columnDefinition = "TEXT")
    private String storyEs;

    private String exportTitleEs;
    private String exportTitleEn;

    @Column(columnDefinition = "TEXT")
    private String exportBodyEs;

    @Column(columnDefinition = "TEXT")
    private String exportBodyEn;

    private Double reputationScore = 4.0;

    private LocalDateTime lastUpdated;

    public ProductPassport() {}

    public ProductPassport(Long id, String productId, String publicId, String farmName,
                           String productName, String productLocation, String storyEs,
                           String exportTitleEs, String exportTitleEn, String exportBodyEs,
                           String exportBodyEn, Double reputationScore, LocalDateTime lastUpdated) {
        this.id = id;
        this.productId = productId;
        this.publicId = publicId;
        this.farmName = farmName;
        this.productName = productName;
        this.productLocation = productLocation;
        this.storyEs = storyEs;
        this.exportTitleEs = exportTitleEs;
        this.exportTitleEn = exportTitleEn;
        this.exportBodyEs = exportBodyEs;
        this.exportBodyEn = exportBodyEn;
        this.reputationScore = reputationScore;
        this.lastUpdated = lastUpdated;
    }

    @PrePersist
    @PreUpdate
    public void touch() {
        this.lastUpdated = LocalDateTime.now();
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getProductId() { return productId; }
    public void setProductId(String productId) { this.productId = productId; }

    public String getPublicId() { return publicId; }
    public void setPublicId(String publicId) { this.publicId = publicId; }

    public String getFarmName() { return farmName; }
    public void setFarmName(String farmName) { this.farmName = farmName; }

    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName; }

    public String getProductLocation() { return productLocation; }
    public void setProductLocation(String productLocation) { this.productLocation = productLocation; }

    public String getStoryEs() { return storyEs; }
    public void setStoryEs(String storyEs) { this.storyEs = storyEs; }

    public String getExportTitleEs() { return exportTitleEs; }
    public void setExportTitleEs(String exportTitleEs) { this.exportTitleEs = exportTitleEs; }

    public String getExportTitleEn() { return exportTitleEn; }
    public void setExportTitleEn(String exportTitleEn) { this.exportTitleEn = exportTitleEn; }

    public String getExportBodyEs() { return exportBodyEs; }
    public void setExportBodyEs(String exportBodyEs) { this.exportBodyEs = exportBodyEs; }

    public String getExportBodyEn() { return exportBodyEn; }
    public void setExportBodyEn(String exportBodyEn) { this.exportBodyEn = exportBodyEn; }

    public Double getReputationScore() { return reputationScore; }
    public void setReputationScore(Double reputationScore) { this.reputationScore = reputationScore; }

    public LocalDateTime getLastUpdated() { return lastUpdated; }
    public void setLastUpdated(LocalDateTime lastUpdated) { this.lastUpdated = lastUpdated; }
}
