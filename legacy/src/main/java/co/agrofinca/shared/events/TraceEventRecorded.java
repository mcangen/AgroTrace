package co.agrofinca.shared.events;

import co.agrofinca.traceability.TraceEvent;

public record TraceEventRecorded(
        TraceEvent traceEvent,
        String farmName,
        String productName,
        String productPublicId
) {}
