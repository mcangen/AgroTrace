package co.agrofinca.farm;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "farms")
public class Farm {

    @Id
    private String id;
    private String name;
    private String location;
    private String ownerName;

    public Farm() {}

    public Farm(String id, String name, String location, String ownerName) {
        this.id = id;
        this.name = name;
        this.location = location;
        this.ownerName = ownerName;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getLocation() { return location; }
    public void setLocation(String location) { this.location = location; }

    public String getOwnerName() { return ownerName; }
    public void setOwnerName(String ownerName) { this.ownerName = ownerName; }
}
