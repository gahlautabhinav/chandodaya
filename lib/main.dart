import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:image_picker/image_picker.dart';

import 'core/services/api_service.dart';
import 'features/analysis_result/view/analysis_result_screen.dart';

void main() {
  runApp(const ChandaApp());
}

/// Supported UI languages
enum AppLanguage { english, hindi, sanskrit }

class ChandaApp extends StatefulWidget {
  const ChandaApp({super.key});

  @override
  State<ChandaApp> createState() => _ChandaAppState();
}

class _ChandaAppState extends State<ChandaApp> {
  ThemeMode _themeMode = ThemeMode.dark;
  AppLanguage _language = AppLanguage.hindi;

  void _toggleTheme() {
    setState(() {
      _themeMode =
          _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    });
  }

  void _setLanguage(AppLanguage lang) {
    setState(() {
      _language = lang;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'छंद विश्लेषण',
      debugShowCheckedModeBanner: false,
      themeMode: _themeMode,
      darkTheme: ThemeData(
        fontFamily: 'Poppins',
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF111111),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFFFFB74D),
          secondary: Color(0xFFFFB74D),
        ),
      ),
      theme: ThemeData(
        fontFamily: 'Poppins',
        brightness: Brightness.light,
        scaffoldBackgroundColor: const Color(0xFFF6F6F6),
        colorScheme: const ColorScheme.light(
          primary: Color(0xFFFFB74D),
          secondary: Color(0xFFFFB74D),
        ),
      ),
      home: HomeScreen(
        language: _language,
        onLanguageChanged: _setLanguage,
        isDark: _themeMode == ThemeMode.dark,
        onToggleTheme: _toggleTheme,
      ),
    );
  }
}

/// Simple chat message model
class ChatMessage {
  final String text;
  final bool fromTeacher;

  ChatMessage({required this.text, required this.fromTeacher});
}

/// Teacher “mood” for status line
enum TeacherMood { welcome, thinking, explaining, appreciating }

class HomeScreen extends StatefulWidget {
  final AppLanguage language;
  final void Function(AppLanguage) onLanguageChanged;
  final bool isDark;
  final VoidCallback onToggleTheme;

  const HomeScreen({
    super.key,
    required this.language,
    required this.onLanguageChanged,
    required this.isDark,
    required this.onToggleTheme,
  });

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _controller = TextEditingController();
  final ApiService _api = ApiService();
  final ImagePicker _imagePicker = ImagePicker();

  bool loading = false;
  bool _isProcessing = false;

  TeacherMood _mood = TeacherMood.welcome;
  final List<ChatMessage> _messages = [];

  /// last analysis result from backend (for “Detailed explanation”)
  Map<String, dynamic>? _lastResult;

  @override
  void initState() {
    super.initState();
    _messages.add(ChatMessage(fromTeacher: true, text: _initialWelcomeText()));
  }

  @override
  void didUpdateWidget(HomeScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    // When language changes, keep chat but add a fresh instruction
    if (oldWidget.language != widget.language) {
      setState(() {
        _messages.add(
          ChatMessage(fromTeacher: true, text: _initialWelcomeText()),
        );
      });
    }
  }

  // ───────────────────────── TEXT HELPERS (multi-language) ─────────────────────────

  String _initialWelcomeText() {
    switch (widget.language) {
      case AppLanguage.english:
        return "Namaste, student! 👋\nType your mantra or shloka here and I’ll explain its chandas step by step.";
      case AppLanguage.hindi:
        return "नमस्ते शिष्य! 👋\nअपना मन्त्र या श्लोक यहाँ लिखिए,\nमैं उसके छंद को चरण-ब-चरण बताऊँगी।";
      case AppLanguage.sanskrit:
        return "नमस्ते शिष्य! 👋\nअत्र स्वं मन्त्रं वा श्लोकं लिख, अहं तस्य छन्दः क्रमशः दर्शयामि।";
    }
  }

  String _hintText() {
    switch (widget.language) {
      case AppLanguage.english:
        return "Type your mantra or shloka…";
      case AppLanguage.hindi:
        return "यहाँ मन्त्र या श्लोक लिखिए…";
      case AppLanguage.sanskrit:
        return "अत्र मन्त्रं वा श्लोकं लिख…";
    }
  }

  String _thinkingLine() {
    switch (widget.language) {
      case AppLanguage.english:
        return "Nice mantra! 🤔\nLet me analyze its words, syllables, laghu–guru pattern and chandas…";
      case AppLanguage.hindi:
        return "अच्छा मन्त्र है! 🤔\nअब मैं इसके पद-भेद, वर्ण-विभाजन, लघु–गुरु और छंद का विश्लेषण करती हूँ…";
      case AppLanguage.sanskrit:
        return "साधु मन्त्रः! 🤔\nइदानीं पदानि, वर्णान्, लघु–गुरु-क्रमं च छन्दश्च निरीक्षे।";
    }
  }

  String _analysisReadyLine() {
    switch (widget.language) {
      case AppLanguage.english:
        return "Well done! 👏\nI’ve identified the chandas pattern. Tap “Detailed explanation” for full breakdown.";
      case AppLanguage.hindi:
        return "शाबाश! 👏\nछंद-पैटर्न निर्धारित हो गया है। “Detailed explanation” दबाकर पूरा विवरण देख सकते हैं।";
      case AppLanguage.sanskrit:
        return "साधु साधु! 👏\nछन्दः निरूपितः। विस्तृत-विवरणं द्रष्टुं “Detailed explanation” नुद।";
    }
  }

  String _invalidInputLine() {
    switch (widget.language) {
      case AppLanguage.english:
        return "This doesn’t look like a proper mantra or verse.\nPlease enter Sanskrit (Devanagari) or a meaningful romanized mantra/shloka (e.g. \"Om Bhur Bhuvah\", \"Tat Savitur Varenyam\"), not random letters, numbers or symbols.";
      case AppLanguage.hindi:
        return "यह इनपुट किसी मन्त्र या छंद जैसा नहीं लग रहा।\nकृपया केवल संस्कृत (देवनागरी) या अर्थपूर्ण रोमनाक्षर मन्त्र/श्लोक लिखिए (जैसे \"Om Bhur Bhuvah\", \"Tat Savitur Varenyam\"),\nयादृच्छिक अक्षर, संख्या या symbol न डालें।";
      case AppLanguage.sanskrit:
        return "एतत् प्रवेशितं न मन्त्रवत् न वा छन्दोबद्धं दृश्यते।\nकृपया देवनागरी-संस्कृतं वा अर्थपूर्णं रोमन-लिप्यां मन्त्रं श्लोकं वा लिख, न तु केवलं आकस्मिक-अक्षर-सङ्ख्या-चिह्नानि।";
    }
  }

  String _errorLine() {
    switch (widget.language) {
      case AppLanguage.english:
        return "Some technical issue occurred. Please try again.";
      case AppLanguage.hindi:
        return "कुछ तकनीकी समस्या आ गई। कृपया दोबारा प्रयास करें।";
      case AppLanguage.sanskrit:
        return "काचित् तन्त्रदोषा जाता। पुनः प्रयासं कुरु।";
    }
  }

  String _moodText() {
    switch (_mood) {
      case TeacherMood.welcome:
        switch (widget.language) {
          case AppLanguage.english:
            return "Teacher is ready 😊";
          case AppLanguage.hindi:
            return "शिक्षिका तैयार है 😊";
          case AppLanguage.sanskrit:
            return "शिक्षिका सज्जा अस्ति 😊";
        }
      case TeacherMood.thinking:
        switch (widget.language) {
          case AppLanguage.english:
            return "Thinking… 🤔";
          case AppLanguage.hindi:
            return "सोच रही हूँ… 🤔";
          case AppLanguage.sanskrit:
            return "चिन्तयामि… 🤔";
        }
      case TeacherMood.explaining:
        switch (widget.language) {
          case AppLanguage.english:
            return "Explaining… 📘";
          case AppLanguage.hindi:
            return "समझा रही हूँ… 📘";
          case AppLanguage.sanskrit:
            return "विवृणोमि… 📘";
        }
      case TeacherMood.appreciating:
        switch (widget.language) {
          case AppLanguage.english:
            return "Great work! 👏";
          case AppLanguage.hindi:
            return "बहुत अच्छा! 👏";
          case AppLanguage.sanskrit:
            return "अति उत्तमम्! 👏";
        }
    }
  }

  // ───────────────────────── INPUT VALIDATION & DOUBT DETECTION ─────────────────────────

  bool _isLikelyValidMantra(String input) {
    final text = input.trim();
    if (text.length < 4) return false;

    final noSpace = text.replaceAll(RegExp(r'\s+'), '');
    if (noSpace.isEmpty) return false;

    final runes = text.runes.toList();
    bool hasDevanagari = false;
    bool hasLetter = false;

    for (final cp in runes) {
      if (cp >= 0x0900 && cp <= 0x097F) {
        hasDevanagari = true;
        hasLetter = true;
      } else {
        final ch = String.fromCharCode(cp);
        if (RegExp(r'[A-Za-z]').hasMatch(ch)) {
          hasLetter = true;
        }
      }
    }

    if (!hasLetter) return false;

    final lettersCount =
        RegExp(r'[A-Za-z\u0900-\u097F]').allMatches(text).length;
    final digitsCount = RegExp(r'\d').allMatches(text).length;
    final symbolsCount =
        RegExp(r'[^\w\s\u0900-\u097F]').allMatches(text).length;

    final totalChars = noSpace.length;
    if (totalChars == 0) return false;

    // Reject if mostly digits/symbols
    if ((digitsCount + symbolsCount) / totalChars > 0.4) return false;

    final isLatinOnly =
        !hasDevanagari && RegExp(r'^[A-Za-z\s]+$').hasMatch(text);
    if (isLatinOnly) {
      final words =
          text.split(RegExp(r'\s+')).where((w) => w.isNotEmpty).toList();
      if (words.length < 2) {
        // reject single random word like "abcdef"
        return false;
      }
    }

    return true;
  }

  /// If the user is asking a "doubt" question, return the YouTube link to suggest.
  String? _detectDoubtHelp(String text) {
    final lower = text.toLowerCase();

    final hasDoubtWord = lower.contains('doubt') ||
        lower.contains('confused') ||
        lower.contains('samajh') ||
        lower.contains('समझ') ||
        lower.contains('शंका') ||
        lower.contains('संशय');

    if (!hasDoubtWord) return null;

    final hasGana = lower.contains('gana') ||
        lower.contains('gaṇa') ||
        lower.contains('गण');

    final hasChanda = lower.contains('chanda') ||
        lower.contains('chandas') ||
        lower.contains('छंद') ||
        lower.contains('छन्द');

    if (hasGana) {
      // doubt on gaṇa
      return 'https://www.youtube.com/watch?v=xRI0MjR4dRI&list=PLmozlYyYE-ERI52EVhtqsdpTUBKf7IoAd&index=3';
    } else if (hasChanda) {
      // doubt on types of chandas
      return 'https://www.youtube.com/watch?v=9yFCNvpaVVA&list=PLmozlYyYE-ERI52EVhtqsdpTUBKf7IoAd&index=4';
    } else {
      // any other doubt
      return 'https://www.youtube.com/watch?v=An16wmqMCvs&list=PLmozlYyYE-ERI52EVhtqsdpTUBKf7IoAd';
    }
  }

  String _doubtReplyText(String url) {
    switch (widget.language) {
      case AppLanguage.english:
        return "You mentioned you have a doubt.\nThis video may help you a lot:\n$url";
      case AppLanguage.hindi:
        return "आपने बताया कि आपको शंका है।\nयह वीडियो आपकी काफी मदद कर सकता है:\n$url";
      case AppLanguage.sanskrit:
        return "त्वया उक्तं यत् शङ्का अस्ति।\nएतद् वीडियो भवतः साहाय्यं करोतु:\n$url";
    }
  }

  // Try to read a chandas name from backend JSON
  String? _extractChandasName(Map<String, dynamic> result) {
    // Examples of possible structures — tweak as your backend actually returns.
    if (result['chandas_name'] is String) {
      return result['chandas_name'] as String;
    }
    if (result['chandas'] is String) {
      return result['chandas'] as String;
    }
    if (result['identifiedChandas'] is Map<String, dynamic>) {
      final m = result['identifiedChandas'] as Map<String, dynamic>;
      if (m['name'] is String) return m['name'] as String;
    }
    if (result['chandas'] is Map<String, dynamic>) {
      final m = result['chandas'] as Map<String, dynamic>;
      if (m['name'] is String) return m['name'] as String;
    }
    return null;
  }

  // ───────────────────────── SEND / ANALYSIS FLOW ─────────────────────────

  Future<void> _handleSend() async {
    final rawText = _controller.text;
    final text = rawText.trim();
    if (text.isEmpty || _isProcessing) return;

    // First, show the user message
    setState(() {
      _messages.add(ChatMessage(fromTeacher: false, text: text));
      _controller.clear();
    });

    // 1) Check if it's a “doubt” question → suggest YouTube, no backFend call
    final yt = _detectDoubtHelp(text);
    if (yt != null) {
      setState(() {
        _messages.add(
          ChatMessage(fromTeacher: true, text: _doubtReplyText(yt)),
        );
      });
      return;
    }

    // 2) Validate as mantra / shloka / poem
    if (!_isLikelyValidMantra(text)) {
      setState(() {
        _messages.add(
          ChatMessage(fromTeacher: true, text: _invalidInputLine()),
        );
      });
      return;
    }

    // 3) Proceed with backend analysis
    setState(() {
      _isProcessing = true;
      loading = true;
      _mood = TeacherMood.thinking;
      _lastResult = null;
    });

    await Future.delayed(const Duration(seconds: 1));

    setState(() {
      _mood = TeacherMood.explaining;
      _messages.add(
        ChatMessage(fromTeacher: true, text: _thinkingLine()),
      );
    });

    try {
      final result = await _api.analyzeMantra(text);
_lastResult = result;

      // try to read chandas name from JSON
      final chandasName = _extractChandasName(result);
      String chandasLine;
      if (chandasName != null && chandasName.trim().isNotEmpty) {
        switch (widget.language) {
          case AppLanguage.english:
            chandasLine =
                "I detected this chandas for your mantra: **$chandasName**.";
            break;
          case AppLanguage.hindi:
            chandasLine =
                "आपके मन्त्र के लिए यह छंद मिला है: **$chandasName**.";
            break;
          case AppLanguage.sanskrit:
            chandasLine =
                "तव मन्त्रस्य छन्दोऽयं लब्धः: **$chandasName**.";
            break;
        }
      } else {
        switch (widget.language) {
          case AppLanguage.english:
            chandasLine =
                "I have identified a classical chandas pattern for your mantra.";
            break;
          case AppLanguage.hindi:
            chandasLine =
                "आपके मन्त्र के लिए पारम्परिक छंद-पैटर्न निर्धारित हो गया है।";
            break;
          case AppLanguage.sanskrit:
            chandasLine =
                "तव मन्त्रस्य पारम्परिकः कश्चन छन्दः उपलक्षितः।";
            break;
        }
      }

      setState(() {
        _mood = TeacherMood.appreciating;
        _messages.add(ChatMessage(fromTeacher: true, text: chandasLine));
        _messages.add(
          ChatMessage(fromTeacher: true, text: _analysisReadyLine()),
        );
      });
    } catch (e) {
  final err = e.toString(); // e.g. "Exception: HTTP 502: Bad Gateway"

  // Extract just the status text if you want it super clean
  String shortError = err;
  final idx = err.indexOf('HTTP');
  if (idx != -1) {
    shortError = err.substring(idx); // "HTTP 502: Bad Gateway"
  }

  setState(() {
    _messages.add(
      ChatMessage(
        fromTeacher: true,
        text: "${_errorLine()}\n\n($shortError)",
      ),
    );
    _mood = TeacherMood.welcome;
    _lastResult = null;
  });
}
 finally {
      if (mounted) {
        setState(() {
          loading = false;
          _isProcessing = false;
        });
      }
    }
  }

  // ───────────────────────── ATTACHMENTS ( + menu ) ─────────────────────────

  void _openAttachmentMenu() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Theme.of(context).colorScheme.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(18)),
      ),
      builder: (context) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.insert_drive_file_outlined),
                title: const Text('Upload image / PDF'),
                onTap: () {
                  Navigator.pop(context);
                  _pickFile();
                },
              ),
              ListTile(
                leading: const Icon(Icons.photo_library_outlined),
                title: const Text('Pick image from gallery'),
                onTap: () {
                  Navigator.pop(context);
                  _pickImageFromGallery();
                },
              ),
              ListTile(
                leading: const Icon(Icons.photo_camera_outlined),
                title: const Text('Open camera'),
                onTap: () {
                  Navigator.pop(context);
                  _captureImageWithCamera();
                },
              ),
              const SizedBox(height: 8),
            ],
          ),
        );
      },
    );
  }

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'png', 'jpg', 'jpeg'],
    );

    if (result != null && result.files.isNotEmpty) {
      final file = result.files.first;
      setState(() {
        _messages.add(
          ChatMessage(
            fromTeacher: false,
            text: '📎 Selected file: ${file.name}',
          ),
        );
        _messages.add(
          ChatMessage(
            fromTeacher: true,
            text:
                'मैं इस फ़ाइल (image/PDF) से मन्त्र को पढ़ने की कोशिश कर सकती हूँ — जब backend पर OCR जोड़ा जाएगा।',
          ),
        );
      });
      // TODO: send file.path to backend when file-based analysis is ready.
    }
  }

  Future<void> _pickImageFromGallery() async {
    final XFile? image =
        await _imagePicker.pickImage(source: ImageSource.gallery);

    if (image != null) {
      setState(() {
        _messages.add(
          ChatMessage(
            fromTeacher: false,
            text: '🖼 Selected image from gallery:\n${image.name}',
          ),
        );
        _messages.add(
          ChatMessage(
            fromTeacher: true,
            text:
                'इस चित्र से मन्त्र पढ़कर छंद निकालने का प्रयास backend पर किया जा सकेगा (जब आप OCR जोड़ेंगे)।',
          ),
        );
      });
      // TODO: send image.path to backend.
    }
  }

  Future<void> _captureImageWithCamera() async {
    final XFile? photo =
        await _imagePicker.pickImage(source: ImageSource.camera);

    if (photo != null) {
      setState(() {
        _messages.add(
          ChatMessage(
            fromTeacher: false,
            text: '📷 Captured image from camera:\n${photo.name}',
          ),
        );
        _messages.add(
          ChatMessage(
            fromTeacher: true,
            text:
                'कैमरा से ली गई छवि से भी मन्त्र-विश्लेषण सम्भव होगा (backend OCR के बाद)।',
          ),
        );
      });
      // TODO: send photo.path to backend.
    }
  }

  // ───────────────────────── UI HELPERS ─────────────────────────

  Widget _buildMessageBubble(ChatMessage msg) {
    final isTeacher = msg.fromTeacher;
    final alignment =
        isTeacher ? Alignment.centerLeft : Alignment.centerRight;

    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final darkTeacher = const Color(0xFF1E1E1E);
    final darkUser = const Color(0xFFFFB74D);
    final lightTeacher = Colors.grey.shade200;
    final lightUser = const Color(0xFFFFB74D);

    final bubbleColor = isTeacher
        ? (isDark ? darkTeacher : lightTeacher)
        : (isDark ? darkUser : lightUser);

    final textColor = isTeacher
        ? (isDark ? Colors.white : Colors.black87)
        : Colors.black;

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      alignment: alignment,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 320),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: bubbleColor,
            borderRadius: BorderRadius.only(
              topLeft: const Radius.circular(16),
              topRight: const Radius.circular(16),
              bottomLeft:
                  isTeacher ? const Radius.circular(0) : const Radius.circular(16),
              bottomRight:
                  isTeacher ? const Radius.circular(16) : const Radius.circular(0),
            ),
          ),
          child: Text(
            msg.text,
            style: TextStyle(fontSize: 13.5, color: textColor),
          ),
        ),
      ),
    );
  }

  Widget _buildInputBar() {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF111111) : Colors.white,
        border: const Border(
          top: BorderSide(color: Colors.black12),
        ),
      ),
      child: Row(
        children: [
          IconButton(
            onPressed: _openAttachmentMenu,
            icon: const Icon(Icons.add, size: 22),
          ),
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              decoration: BoxDecoration(
                color: isDark ? const Color(0xFF1E1E1E) : Colors.grey.shade100,
                borderRadius: BorderRadius.circular(30),
                border: Border.all(
                  color: isDark ? Colors.grey.shade800 : Colors.grey.shade400,
                ),
              ),
              child: TextField(
                controller: _controller,
                minLines: 1,
                maxLines: 4,
                decoration: InputDecoration(
                  hintText: _hintText(),
                  border: InputBorder.none,
                  hintStyle: const TextStyle(color: Colors.grey),
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          InkWell(
            onTap: loading ? null : _handleSend,
            borderRadius: BorderRadius.circular(40),
            child: Container(
              padding: const EdgeInsets.all(10),
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                color: Color(0xFFFFB74D),
              ),
              child: loading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.black,
                      ),
                    )
                  : const Icon(Icons.send_rounded, color: Colors.black),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLanguageDropdown() {
    return DropdownButton<AppLanguage>(
      value: widget.language,
      underline: const SizedBox(),
      icon: const Icon(Icons.language, size: 20),
      items: const [
        DropdownMenuItem(
          value: AppLanguage.english,
          child: Text('English'),
        ),
        DropdownMenuItem(
          value: AppLanguage.hindi,
          child: Text('Hindi'),
        ),
        DropdownMenuItem(
          value: AppLanguage.sanskrit,
          child: Text('Sanskrit'),
        ),
      ],
      onChanged: (val) {
        if (val != null) {
          widget.onLanguageChanged(val);
          // HomeScreen reacts in didUpdateWidget (adds new welcome message)
        }
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final moodText = _moodText();

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Top bar: title + mood + language + theme toggle
            Padding(
              padding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Row(
                children: [
                  // If you want to use your Om PNG logo, replace this Icon with:
                  // Image.asset('assets/logo/om.png', height: 28, width: 28),
                  const Icon(Icons.school_outlined, color: Color(0xFFFFB74D)),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          "छंद शिक्षिका",
                          style: TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        Text(
                          moodText,
                          style: const TextStyle(
                            fontSize: 12,
                            color: Colors.grey,
                          ),
                        ),
                      ],
                    ),
                  ),
                  _buildLanguageDropdown(),
                  IconButton(
                    onPressed: widget.onToggleTheme,
                    icon: Icon(
                      widget.isDark
                          ? Icons.light_mode_outlined
                          : Icons.dark_mode_outlined,
                    ),
                    tooltip: 'Toggle theme',
                  ),
                ],
              ),
            ),

            const Divider(height: 1, color: Colors.black26),

            // Chat list
            Expanded(
              child: ListView.builder(
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                itemCount: _messages.length,
                itemBuilder: (context, index) =>
                    _buildMessageBubble(_messages[index]),
              ),
            ),

            // “Detailed explanation” button (only when a backend result exists)
            if (_lastResult != null)
              Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                child: Align(
                  alignment: Alignment.centerRight,
                  child: OutlinedButton.icon(
                    onPressed: () {
                      final result = _lastResult!;
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => AnalysisResultScreen(result: result),
                        ),
                      );
                    },
                    icon: const Icon(Icons.open_in_new, size: 18),
                    label: const Text('Detailed explanation'),
                  ),
                ),
              ),

            // Input bar
            _buildInputBar(),
          ],
        ),
      ),
    );
  }
}
