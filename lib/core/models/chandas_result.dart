class ChandasResult {
  final String requestId;
  final String devanagariText;

  final MantraSwaraStatus mantraSwaraStatus;

  final IdentifiedChandas identifiedChandas;

  ChandasResult({
    required this.requestId,
    required this.devanagariText,
    required this.mantraSwaraStatus,
    required this.identifiedChandas,
  });

  factory ChandasResult.fromJson(Map<String, dynamic> json) {
    return ChandasResult(
      requestId: json['requestId'],
      devanagariText: json['devanagariText'],
      mantraSwaraStatus:
          MantraSwaraStatus.fromJson(json['mantraSwaraStatus']),
      identifiedChandas:
          IdentifiedChandas.fromJson(json['identifiedChandas']),
    );
  }
}

class MantraSwaraStatus {
  final bool hasSvaras;
  final String complexity;
  final String? note;

  MantraSwaraStatus({
    required this.hasSvaras,
    required this.complexity,
    this.note,
  });

  factory MantraSwaraStatus.fromJson(Map<String, dynamic> json) {
    return MantraSwaraStatus(
      hasSvaras: json['hasSvaras'],
      complexity: json['complexity'],
      note: json['note'],
    );
  }
}

class IdentifiedChandas {
  final String name;
  final double confidence;

  IdentifiedChandas({
    required this.name,
    required this.confidence,
  });

  factory IdentifiedChandas.fromJson(Map<String, dynamic> json) {
    return IdentifiedChandas(
      name: json['name'],
      confidence: (json['confidence'] ?? 0).toDouble(),
    );
  }
}
