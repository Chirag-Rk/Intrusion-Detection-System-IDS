import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { theme } from '../theme';
import { API_BASE_URL } from '../config';

export default function AdaptiveLearningScreen() {
  const [samples, setSamples] = useState([]);
  const [loading, setLoading] = useState(true);
  const [retraining, setRetraining] = useState(false);
  const [retrainMsg, setRetrainMsg] = useState('');

  const fetchSamples = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/verified-samples`);
      const data = await res.json();
      setSamples(data.samples || []);
    } catch (e) {
      console.log('Error fetching verified samples:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSamples();
  }, []);

  const handleRetrain = async () => {
    setRetraining(true);
    setRetrainMsg('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/retrain`, { method: 'POST' });
      const data = await res.json();
      setRetrainMsg(data.message || (data.success ? 'Retraining successful!' : 'Retraining complete.'));
    } catch (e) {
      setRetrainMsg('Error triggering retraining.');
    } finally {
      setRetraining(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>🧠 Controlled Adaptive Retraining</Text>
        <Text style={styles.subtitle}>
          Safely adapt to newly verified zero-day intrusions with human-in-the-loop analyst validation and automatic candidate rejection safeguards.
        </Text>
      </View>

      {/* Retraining Action Card */}
      <View style={styles.actionCard}>
        <Text style={styles.actionTitle}>Active Model Version: <Text style={styles.versionText}>AegisDNN-v1.0.0</Text></Text>
        <Text style={styles.actionDesc}>
          Retraining merges baseline training corpora with verified zero-day anomalies, evaluating on validation sets before deployment.
        </Text>

        <TouchableOpacity
          style={[styles.retrainBtn, retraining && { opacity: 0.6 }]}
          onPress={handleRetrain}
          disabled={retraining}
        >
          {retraining ? (
            <ActivityIndicator color="#0A0E1A" />
          ) : (
            <Text style={styles.retrainBtnText}>⚡ Trigger Controlled Model Retrain</Text>
          )}
        </TouchableOpacity>

        {retrainMsg ? (
          <View style={styles.msgBox}>
            <Text style={styles.msgText}>{retrainMsg}</Text>
          </View>
        ) : null}
      </View>

      {/* Verified Samples Log */}
      <Text style={styles.sectionTitle}>Candidate Verification Queue</Text>
      {samples.length === 0 ? (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyText}>No pending anomaly samples in the verification queue.</Text>
          <Text style={styles.emptySub}>Anomalies flagged during live monitoring will populate here for analyst review.</Text>
        </View>
      ) : (
        samples.map((s, idx) => (
          <View key={idx} style={styles.sampleCard}>
            <View style={styles.sampleHeader}>
              <Text style={styles.sampleId}>Sample #{s.id || idx + 1}</Text>
              <View style={[styles.statusBadge, s.status === 'VERIFIED' ? styles.statusVerified : styles.statusPending]}>
                <Text style={styles.statusBadgeText}>{s.status || 'PENDING'}</Text>
              </View>
            </View>
            <Text style={styles.sampleMeta}>Detected Anomaly: {s.predicted_label || 'Zero-Day Pattern'}</Text>
            <Text style={styles.sampleDate}>Timestamp: {s.timestamp || 'Recent'}</Text>
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.bg },
  content: { padding: 20, paddingBottom: 60 },
  header: { marginBottom: 20 },
  title: { fontSize: 22, fontWeight: '800', color: theme.colors.text },
  subtitle: { fontSize: 13, color: theme.colors.textMuted, marginTop: 4, lineHeight: 18 },
  actionCard: {
    backgroundColor: theme.colors.card,
    borderRadius: 14,
    padding: 20,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    marginBottom: 24,
  },
  actionTitle: { fontSize: 15, fontWeight: '700', color: theme.colors.text, marginBottom: 8 },
  versionText: { color: theme.colors.primary, fontWeight: '800' },
  actionDesc: { fontSize: 12, color: theme.colors.textMuted, lineHeight: 18, marginBottom: 16 },
  retrainBtn: {
    backgroundColor: theme.colors.primary,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  retrainBtnText: { color: '#0A0E1A', fontWeight: '800', fontSize: 14 },
  msgBox: { backgroundColor: theme.colors.surface, padding: 12, borderRadius: 8, marginTop: 12 },
  msgText: { color: theme.colors.primary, fontSize: 12, fontWeight: '600' },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: theme.colors.text, marginBottom: 12 },
  emptyCard: {
    backgroundColor: theme.colors.card,
    padding: 24,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
  },
  emptyText: { color: theme.colors.text, fontSize: 14, fontWeight: '600', marginBottom: 4 },
  emptySub: { color: theme.colors.textMuted, fontSize: 12, textAlign: 'center' },
  sampleCard: {
    backgroundColor: theme.colors.card,
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
  },
  sampleHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  sampleId: { fontSize: 14, fontWeight: '800', color: theme.colors.text },
  statusBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6 },
  statusVerified: { backgroundColor: 'rgba(0, 229, 153, 0.2)' },
  statusPending: { backgroundColor: 'rgba(255, 184, 0, 0.2)' },
  statusBadgeText: { fontSize: 10, fontWeight: '800', color: theme.colors.text },
  sampleMeta: { fontSize: 12, color: theme.colors.textMuted, marginBottom: 2 },
  sampleDate: { fontSize: 11, color: theme.colors.textMuted },
});
