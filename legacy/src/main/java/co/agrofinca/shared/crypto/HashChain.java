package co.agrofinca.shared.crypto;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

public class HashChain {

    public static String hash(String payload, String prevHash) {
        String prev = (prevHash == null || prevHash.isBlank()) ? "GENESIS" : prevHash;
        String input = payload + "|" + prev;
        return sha256Hex(input);
    }

    public static String hashPayloadOnly(String payload) {
        String input = payload + "|PAYLOAD_ONLY";
        return sha256Hex(input);
    }

    private static String sha256Hex(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] bytes = digest.digest(input.getBytes(StandardCharsets.UTF_8));
            HexFormat hex = HexFormat.of();
            return hex.formatHex(bytes);
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("SHA-256 not available", e);
        }
    }
}
