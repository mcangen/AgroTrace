package co.agrofinca.traceability;

public record VerificationResult(boolean ok, Integer brokenIndex, Long brokenEventId) {

    public static VerificationResult clean() {
        return new VerificationResult(true, null, null);
    }
}
