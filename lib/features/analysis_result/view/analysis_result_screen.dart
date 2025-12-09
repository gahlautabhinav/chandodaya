import 'package:flutter/material.dart';

class AnalysisResultScreen extends StatelessWidget {
  final Map<String, dynamic> result;

  const AnalysisResultScreen({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final isDark = theme.brightness == Brightness.dark;

    final input = result['input'] as Map<String, dynamic>? ?? {};
    final normalization =
        result['normalization'] as Map<String, dynamic>? ?? {};

    final textDev = input['text_dev']?.toString() ?? '';
    final normNoSvara = normalization['without_svara']?.toString() ?? '';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Chandas Analysis'),
        centerTitle: true,
        backgroundColor: isDark ? const Color(0xFF1E1E1E) : scheme.primary,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 1. SHLOKA + NORMALIZED
          _buildSection(
            context,
            title: 'Input Śloka',
            child: _buildInputShlokaCard(
              context,
              textWithSvara: textDev,
              textWithoutSvara: normNoSvara,
            ),
          ),

          const SizedBox(height: 16),

          // 2. PADAPATHA
          _buildSection(
            context,
            title: 'Padapāṭha',
            child: _buildPadapatha(
              result['padapatha'] as Map<String, dynamic>?,
            ),
          ),

          const SizedBox(height: 16),

          // 3. SAMHITA PADAS + AKSHARA-WISE
          _buildSection(
            context,
            title: 'Saṁhitā Padas',
            child: _buildSamhitaPadas(
              context,
              result['samhita_padas'] as List<dynamic>?,
            ),
          ),

          const SizedBox(height: 16),

          // 4. FEATURES (without sandhi_profile)
          _buildSection(
            context,
            title: 'Features',
            child: _buildFeatures(
              context,
              result['features'] as Map<String, dynamic>?,
            ),
          ),

          const SizedBox(height: 16),

          // 5. METER RULE-BASED (without notes)
          _buildSection(
            context,
            title: 'Meter (Rule Based)',
            child: _buildMeter(
              context,
              result['meter_rule_based'] as Map<String, dynamic>?,
            ),
          ),

          const SizedBox(height: 16),

          // 6. GOLD / DATASET METER LABEL AT END
          _buildGoldMeter(context, result['meter_gold_raw']),
        ],
      ),
    );
  }

  // ─────────────────────── SECTION WRAPPER ───────────────────────

  Widget _buildSection(BuildContext context,
      {required String title, required Widget child}) {
    final scheme = Theme.of(context).colorScheme;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: scheme.surface.withOpacity(0.9),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: scheme.outline.withOpacity(0.3)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.18),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style:
                const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 10),
          child,
        ],
      ),
    );
  }

  // ─────────────────────── INPUT SHLOKA CARD ───────────────────────

  Widget _buildInputShlokaCard(
    BuildContext context, {
    required String textWithSvara,
    required String textWithoutSvara,
  }) {
    final scheme = Theme.of(context).colorScheme;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            scheme.primary.withOpacity(0.18),
            scheme.surfaceVariant.withOpacity(0.4),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Original (with svara)',
            style: TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            textWithSvara.isNotEmpty ? textWithSvara : '—',
            style: const TextStyle(fontSize: 15),
          ),
          const SizedBox(height: 10),
          const Divider(height: 10),
          const SizedBox(height: 6),
          const Text(
            'Normalized (without svara)',
            style: TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            textWithoutSvara.isNotEmpty ? textWithoutSvara : '—',
            style: const TextStyle(fontSize: 15),
          ),
        ],
      ),
    );
  }

  // ─────────────────────── PADAPATHA ───────────────────────

  Widget _buildPadapatha(Map<String, dynamic>? padapatha) {
    if (padapatha == null ||
        (padapatha['raw'] ?? '').toString().trim().isEmpty) {
      return const Text('No Padapāṭha available.');
    }

    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white24),
      ),
      child: Text(
        padapatha['raw'].toString(),
        style: const TextStyle(fontSize: 15),
      ),
    );
  }

  // ─────────────────────── SAMHITA PADAS ───────────────────────

  Widget _buildSamhitaPadas(
      BuildContext context, List<dynamic>? padasRaw) {
    if (padasRaw == null || padasRaw.isEmpty) {
      return const Text('No Saṁhitā padas available.');
    }

    return Column(
      children: List.generate(padasRaw.length, (i) {
        final p = padasRaw[i] as Map<String, dynamic>;
        final aksharas = p['aksharas'] as List<dynamic>?;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Pada ${p['index']}',
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 16,
              ),
            ),
            const SizedBox(height: 6),

            _buildKeyValueCard([
              ['Text', p['text'].toString()],
              ['LG', p['LG'].toString()],
            ]),

            const SizedBox(height: 10),

            _buildGanaTable(context, p['ganas'] as List<dynamic>?),

            const SizedBox(height: 10),

            const Text(
              'Saṁhitā padas (akshara-wise)',
              style: TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 15,
              ),
            ),
            const SizedBox(height: 6),

            _buildAksharaDataTable(context, aksharas),

            const Divider(height: 28),
          ],
        );
      }),
    );
  }

  Widget _buildKeyValueCard(List<List<String>> rows) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white24),
      ),
      child: Column(
        children: rows
            .map(
              (r) => Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      r[0],
                      style: const TextStyle(fontWeight: FontWeight.w500),
                    ),
                    const Spacer(),
                    Flexible(
                      flex: 3,
                      child: Text(
                        r[1],
                        textAlign: TextAlign.right,
                        style: const TextStyle(fontSize: 14),
                      ),
                    ),
                  ],
                ),
              ),
            )
            .toList(),
      ),
    );
  }

  // ─────────────────────── GANA TABLE ───────────────────────

  Widget _buildGanaTable(BuildContext context, List<dynamic>? ganas) {
    if (ganas == null || ganas.isEmpty) {
      return const Text('No gaṇas detected.');
    }

    final scheme = Theme.of(context).colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Gaṇas',
          style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
        ),
        const SizedBox(height: 6),
        Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.white24),
          ),
          child: DataTable(
            headingRowColor: MaterialStateProperty.all(
              scheme.primary.withOpacity(0.18),
            ),
            columnSpacing: 20,
            dataRowMinHeight: 32,
            dataRowMaxHeight: 40,
            columns: const [
              DataColumn(label: Text('Index')),
              DataColumn(label: Text('Gaṇa')),
            ],
            rows: List.generate(
              ganas.length,
              (i) => DataRow(
                cells: [
                  DataCell(Text(i.toString())),
                  DataCell(Text(ganas[i].toString())),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  // ─────────────────────── AKSHARA TABLE (WITH L/G COLORS) ───────────────────────

  Widget _buildAksharaDataTable(
      BuildContext context, List<dynamic>? aksharasRaw) {
    if (aksharasRaw == null || aksharasRaw.isEmpty) {
      return const Text('No akṣara data found.');
    }

    final scheme = Theme.of(context).colorScheme;

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white24),
        ),
        child: DataTable(
          headingRowColor: MaterialStateProperty.all(
            scheme.secondary.withOpacity(0.18),
          ),
          columnSpacing: 18,
          dataRowMinHeight: 32,
          dataRowMaxHeight: 40,
          columns: const [
            DataColumn(label: Text('#')),
            DataColumn(label: Text('Text')),
            DataColumn(label: Text('Vowel')),
            DataColumn(label: Text('L/G')),
            DataColumn(label: Text('Guru reason')),
            DataColumn(label: Text('Svara')),
          ],
          rows: aksharasRaw.map((raw) {
            final a = raw as Map<String, dynamic>;
            final lg = a['L_or_G']?.toString() ?? '';
            return DataRow(
              cells: [
                DataCell(Text(a['index'].toString())),
                DataCell(
                  ConstrainedBox(
                    constraints: const BoxConstraints(minWidth: 80),
                    child: Text(a['text'].toString()),
                  ),
                ),
                DataCell(Text(a['vowel'].toString())),
                DataCell(_buildLGChip(lg)),
                DataCell(
                  ConstrainedBox(
                    constraints: const BoxConstraints(minWidth: 90),
                    child: Text(
                      a['guru_reason'].toString(),
                      softWrap: true,
                    ),
                  ),
                ),
                DataCell(Text(a['svara'].toString())),
              ],
            );
          }).toList(),
        ),
      ),
    );
  }

  /// Colored chip for L/G
  Widget _buildLGChip(String value) {
    Color bg;
    Color fg;

    if (value == 'L') {
      bg = const Color(0xFF4CAF50); // green
      fg = Colors.white;
    } else if (value == 'G') {
      bg = const Color(0xFFFFB74D); // saffron
      fg = Colors.black;
    } else {
      bg = Colors.grey.shade600;
      fg = Colors.white;
    }

    return Container(
      padding:
          const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        value,
        style: TextStyle(
          color: fg,
          fontWeight: FontWeight.w600,
          fontSize: 12,
        ),
      ),
    );
  }

  // ─────────────────────── FEATURES (WITHOUT sandhi_profile) ───────────────────────

  Widget _buildFeatures(
      BuildContext context, Map<String, dynamic>? features) {
    if (features == null) {
      return const Text('No features available.');
    }

    final filtered = Map<String, dynamic>.from(features)
      ..remove('sandhi_profile');

    if (filtered.isEmpty) {
      return const Text('No features available.');
    }

    final rows = filtered.entries
        .map((e) => [e.key.toString(), e.value.toString()])
        .toList();

    return _buildKeyValueCard(rows);
  }

  // ─────────────────────── METER (WITHOUT notes) ───────────────────────

  Widget _buildMeter(
      BuildContext context, Map<String, dynamic>? meter) {
    if (meter == null) {
      return const Text('No meter information.');
    }

    final filtered = Map<String, dynamic>.from(meter)..remove('notes');

    final rows = filtered.entries
        .map((e) => [e.key.toString(), e.value.toString()])
        .toList();

    return _buildKeyValueCard(rows);
  }

  // ─────────────────────── GOLD METER (DATASET LABEL) ───────────────────────

  Widget _buildGoldMeter(BuildContext context, dynamic meterGoldRaw) {
  final gold = meterGoldRaw?.toString().trim() ?? '';

  if (gold.isEmpty || gold.toLowerCase() == 'none') {
    return const SizedBox.shrink();
  }

  final scheme = Theme.of(context).colorScheme;

  return Container(
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      borderRadius: BorderRadius.circular(16),
      gradient: LinearGradient(
        colors: [
          scheme.primary.withOpacity(0.9),
          scheme.secondary.withOpacity(0.9),
        ],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
      boxShadow: [
        BoxShadow(
          color: Colors.black.withOpacity(0.35),
          blurRadius: 14,
          offset: const Offset(0, 6),
        ),
      ],
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Gold Meter',
          style: TextStyle(
            fontWeight: FontWeight.w700,
            fontSize: 16,
            color: Colors.black,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          gold,
          style: const TextStyle(
            fontSize: 15,
            color: Colors.black,
          ),
        ),
      ],
    ),
  );

  }
}
