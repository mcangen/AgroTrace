package co.agrofinca.traceability;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "trace_events")
public class TraceEvent {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String productId;

    @Column(nullable = false)
    private String eventType;

    @Column(columnDefinition = "TEXT")
    private String payload;

    private String payloadHash;

    private String prevHash;

    private String chainHash;

    @Column(nullable = false)
    private LocalDateTime timestamp;

    public TraceEvent() {}

    public TraceEvent(Long id, String productId, String eventType, String payload,
                      String payloadHash, String prevHash, String chainHash,
                      LocalDateTime timestamp) {
        this.id = id;
        this.productId = productId;
        this.eventType = eventType;
        this.payload = payload;
        this.payloadHash = payloadHash;
        this.prevHash = prevHash;
        this.chainHash = chainHash;
        this.timestamp = timestamp;
    }

    @PrePersist
    public void prePersist() {
        if (this.timestamp == null) {
            this.timestamp = LocalDateTime.now();
        }
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getProductId() { return productId; }
    public void setProductId(String productId) { this.productId = productId; }

    public String getEventType() { return eventType; }
    public void setEventType(String eventType) { this.eventType = eventType; }

    public String getPayload() { return payload; }
    public void setPayload(String payload) { this.payload = payload; }

    public String getPayloadHash() { return payloadHash; }
    public void setPayloadHash(String payloadHash) { this.payloadHash = payloadHash; }

    public String getPrevHash() { return prevHash; }
    public void setPrevHash(String prevHash) { this.prevHash = prevHash; }

    public String getChainHash() { return chainHash; }
    public void setChainHash(String chainHash) { this.chainHash = chainHash; }

    public LocalDateTime getTimestamp() { return timestamp; }
    public void setTimestamp(LocalDateTime timestamp) { this.timestamp = timestamp; }
}
