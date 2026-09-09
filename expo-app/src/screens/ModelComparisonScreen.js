import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { theme } from '../theme';
import { API_BASE_URL } from '../config';

export default function ModelComparisonScreen() {
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchMetrics = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/metrics`);
      const data = await res.json();
      setMetrics(data.metrics || []);
    } catch (e) {
      console.log('Error fetching metrics:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchMetrics(); }} tintColor={theme.colors.primary} />}
    >
      <View style={styles.header}>
        <Text style={styles.title}>📊 Model Evaluation & Benchmarks</Text>
        <Text style={styles.subtitle}>
          Comparative evaluation of Proposed AegisIDS vs Classical Baseline Classifiers on 22,544 test network flows.
        </Text>
      </View>

      {/* Metric Cards */}
      {metrics.map((m, idx) => {
        const isProposed = m.Model.includes('AegisIDS') || m.Model.includes('Proposed');
        const accPct = Math.round(m.Accuracy * 100);
        const f1Pct = Math.round(m['F1-Score'] * 100);
        const recPct = Math.round(m.Recall * 100);
        const fprPct = (m['False Positive Rate (FPR)'] * 100).toFixed(1);

        return (
          <View key={idx} style={[styles.modelCard, isProposed && styles.proposedCard]}>
            <View style={styles.modelHeader}>
              <Text style={[styles.modelName, isProposed && { color: theme.colors.primary }]}>
                {m.Model}
              </Text>
              {isProposed && (
                <View style={styles.proposedBadge}>
                  <Text style={styles.proposedBadgeText}>PROPOSED</Text>
                </View>
              )}
            </View>

            {/* Metric Bars */}
            <View style={styles.metricRow}>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Accuracy</Text>
                <Text style={styles.metricVal}>{(m.Accuracy * 100).toFixed(2)}%</Text>
                <View style={styles.barBg}>
                  <View style={[styles.barFill, { width: `${accPct}%`, backgroundColor: theme.colors.accent }]} />
                </View>
              </View>

              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>F1-Score</Text>
                <Text style={styles.metricVal}>{(m['F1-Score'] * 100).toFixed(2)}%</Text>
                <View style={styles.barBg}>
                  <View style={[styles.barFill, { width: `${f1Pct}%`, backgroundColor: theme.colors.primary }]} />
                </View>
              </View>
            </View>

            <View style={styles.metaRow}>
              <Text style={styles.metaText}>Recall: <Text style={styles.metaVal}>{(m.Recall * 100).toFixed(2)}%</Text></Text>
              <Text style={styles.metaText}>Precision: <Text style={styles.metaVal}>{(m.Precision * 100).toFixed(2)}%</Text></Text>
              <Text style={styles.metaText}>FPR: <Text style={[styles.metaVal, { color: theme.colors.warning }]}>{fprPct}%</Text></Text>
            </View>

            <View style={styles.fnRow}>
              <Text style={styles.fnText}>
                Missed Intrusions (False Negatives): <Text style={[styles.fnVal, isProposed && { color: theme.colors.primary }]}>{m['False Negatives']}</Text>
              </Text>
            </View>
          </View>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.bg },
  content: { padding: 20, paddingBottom: 60 },
  header: { marginBottom: 20 },
  title: { fontSize: 22, fontWeight: '800', color: theme.colors.text },
  subtitle: { fontSize: 13, color: theme.colors.textMuted, marginTop: 4, lineHeight: 18 },
  modelCard: {
    backgroundColor: theme.colors.card,
    borderRadius: 14,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
  },
  proposedCard: {
    borderColor: theme.colors.primary,
    borderWidth: 1.5,
    backgroundColor: '#0E1726',
  },
  modelHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  modelName: { fontSize: 16, fontWeight: '800', color: theme.colors.text },
  proposedBadge: { backgroundColor: theme.colors.primary, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6 },
  proposedBadgeText: { color: '#0A0E1A', fontSize: 10, fontWeight: '900' },
  metricRow: { flexDirection: 'row', gap: 14, marginBottom: 12 },
  metricItem: { flex: 1 },
  metricLabel: { fontSize: 11, color: theme.colors.textMuted, fontWeight: '600' },
  metricVal: { fontSize: 16, fontWeight: '800', color: theme.colors.text, marginVertical: 2 },
  barBg: { height: 6, backgroundColor: theme.colors.surface, borderRadius: 3, overflow: 'hidden' },
  barFill: { height: '100%', borderRadius: 3 },
  metaRow: { flexDirection: 'row', justifyContent: 'space-between', borderTopWidth: 1, borderTopColor: theme.colors.cardBorder, paddingTop: 10, marginBottom: 8 },
  metaText: { fontSize: 12, color: theme.colors.textMuted },
  metaVal: { color: theme.colors.text, fontWeight: '700' },
  fnRow: { backgroundColor: theme.colors.surface, padding: 8, borderRadius: 6 },
  fnText: { fontSize: 11, color: theme.colors.textMuted },
  fnVal: { color: theme.colors.danger, fontWeight: '800' },
});
