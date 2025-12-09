import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiService {
  // TODO — Replace this with YOUR actual Render URL
  // Example: "https://vedic-chandas-api.onrender.com"
  static const String _baseUrl = "https://chandodaya.onrender.com";

  // -----------------------------------------------------------------------------------
  // TEXT ANALYSIS : POST /api/analyze/text
  // -----------------------------------------------------------------------------------

  Future<Map<String, dynamic>> analyzeMantra(String text) async {
    final uri = Uri.parse("$_baseUrl/api/analyze/text");

    final response = await http.post(
      uri,
      headers: { HttpHeaders.contentTypeHeader: "application/json" },
      body: jsonEncode({ "text": text }),
    );

    if (_isSuccess(response.statusCode)) {
      final decoded = _safeDecode(response.body);
      if (decoded is Map<String, dynamic> &&
          decoded["analysis"] is Map<String, dynamic>) {
        return decoded["analysis"];
      }
      return decoded; // fallback
    } else {
      throw Exception(_shortError(response));
    }
  }

  // -----------------------------------------------------------------------------------
  // FILE ANALYSIS : POST /api/analyze/file
  // -----------------------------------------------------------------------------------

  Future<Map<String, dynamic>> analyzeFile(
    String filePath, {
    bool useGemini = true,
  }) async {
    final uri = Uri.parse("$_baseUrl/api/analyze/file");

    final request = http.MultipartRequest("POST", uri);

    request.files.add(await http.MultipartFile.fromPath("file", filePath));
    request.fields["use_gemini"] = useGemini.toString();

    final streamed = await request.send();
    final response = await http.Response.fromStream(streamed);

    if (_isSuccess(response.statusCode)) {
      final decoded = _safeDecode(response.body);
      if (decoded is Map<String, dynamic>) return decoded;
      return { "raw": decoded };
    } else {
      throw Exception(_shortError(response));
    }
  }

  // -----------------------------------------------------------------------------------
  // HELPERS
  // -----------------------------------------------------------------------------------

  bool _isSuccess(int code) => code >= 200 && code < 300;

  /// Prevents Flutter UI from showing giant HTML pages.
  String _shortError(http.Response response) {
    final phrase = response.reasonPhrase?.isNotEmpty == true
        ? response.reasonPhrase
        : "Error";

    return "HTTP ${response.statusCode}: $phrase";
  }

  /// Safe JSON decoding with helpful error if backend throws unexpected output.
  dynamic _safeDecode(String body) {
    try {
      return jsonDecode(body);
    } catch (e) {
      throw Exception("Invalid JSON from server. Body: $body");
    }
  }
}
