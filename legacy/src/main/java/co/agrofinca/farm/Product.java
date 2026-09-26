package co.agrofinca.farm;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDate;

@Entity
@Table(name = "products")
public class Product {

    @Id
    private String id;
    private String farmId;
    private String name;
    private String description;
    private String publicId;
    private String variety;
    private String responsable;
    private String insumos;
    private String postCosecha;
    private LocalDate fechaSiembra;
    private LocalDate fechaCosecha;

    public Product() {}

    public Product(String id, String farmId, String name, String description, String publicId) {
        this.id = id;
        this.farmId = farmId;
        this.name = name;
        this.description = description;
        this.publicId = publicId;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getFarmId() { return farmId; }
    public void setFarmId(String farmId) { this.farmId = farmId; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public String getPublicId() { return publicId; }
    public void setPublicId(String publicId) { this.publicId = publicId; }

    public String getVariety() { return variety; }
    public void setVariety(String variety) { this.variety = variety; }

    public String getResponsable() { return responsable; }
    public void setResponsable(String responsable) { this.responsable = responsable; }

    public String getInsumos() { return insumos; }
    public void setInsumos(String insumos) { this.insumos = insumos; }

    public String getPostCosecha() { return postCosecha; }
    public void setPostCosecha(String postCosecha) { this.postCosecha = postCosecha; }

    public LocalDate getFechaSiembra() { return fechaSiembra; }
    public void setFechaSiembra(LocalDate fechaSiembra) { this.fechaSiembra = fechaSiembra; }

    public LocalDate getFechaCosecha() { return fechaCosecha; }
    public void setFechaCosecha(LocalDate fechaCosecha) { this.fechaCosecha = fechaCosecha; }
}
