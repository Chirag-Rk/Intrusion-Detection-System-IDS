import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Switch } from 'react-native';
import { theme } from '../theme';
import { API_BASE_URL } from '../config';

export default function LiveMonitorScreen() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentRecord, setCurrentRecord] = useState(null);
  const [packetCount, setPacketCount] = useState(0);
  const [recentFeed, setRecentFeed] = useState([]);
  const timerRef = useRef(null);

  const fetchNextSample = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/live-sample`);
      const sample = await res.json();
      setCurrentRecord(sample);
      setPacketCount((prev) => prev + 1);
      setRecentFeed((prev) => [sample, ...prev.slice(0, 7)]);
    } catch (e) {
      console.log('Error fetching live sample:', e);
    }
  };

  useEffect(() => {
    if (isStreaming) {
      fetchNextSample();
      timerRef.current = setInterval(fetchNextSample, 2000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isStreaming]);

  const pred = currentRecord?.prediction;
  const alert = currentRecord?.alert;
  const flow = currentRecord?.flow_features;
  const sevColor = pred ? theme.severityColors[pred.severity] || theme.colors.primary : theme.colors.primary;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Stream Control Header */}
      <View style={styles.controlCard}>
        <View style={styles.controlHeader}>
          <View>
            <Text style={styles.title}>📡 Real-Time Traffic Ingestion</Text>
            <Text style={styles.subtitle}>Packets Processed: {packetCount}</Text>
          </View>
          <View style={styles.switchWrapper}>
            <Text style={[styles.statusText, { color: isStreaming ? theme.colors.primary : theme.colors.textMuted }]}>
              {isStreaming ? 'LIVE' : 'PAUSED'}
            </Text>
            <Switch
              value={isStreaming}
              onValueChange={setIsStreaming}
              trackColor={{ false: theme.colors.surface, true: theme.colors.primary }}
              thumbColor={isStreaming ? '#0A0E1A' : theme.colors.textMuted}
            />
          </View>
        </View>
      </View>

      {/* Active Flow Inspection Card */}
      {currentRecord ? (
        <View style={[styles.card, { borderColor: sevColor }]}>
          <View style={styles.badgeRow}>
            <View style={[styles.badge, { backgroundColor: sevColor }]}>
              <Text style={styles.badgeText}>{pred?.severity || 'NORMAL'}</Text>
            </View>
            <Text style={styles.recordIndex}>Flow #{currentRecord.index}</Text>
          </View>

          <View style={styles.scoreRow}>
            <View style={styles.scoreBox}>
              <Text style={styles.scoreLabel}>Threat Score</Text>
              <Text style={[styles.scoreValue, { color: sevColor }]}>
                {pred?.threat_score || 0}
                <Text style={styles.scoreMax}> /100</Text>
              </Text>
            </View>
            <View style={styles.scoreBox}>
              <Text style={styles.scoreLabel}>Decision</Text>
              <Text style={styles.decisionValue}>{pred?.decision || 'Analyzing...'}</Text>
            </View>
          </View>

          {/* Alert Notice if Present */}
          {alert && (
            <View style={styles.alertBanner}>
              <Text style={styles.alertTitle}>🚨 {alert['Alert ID']} — Intrusion Detected</Text>
              <Text style={styles.alertRec}>{alert.Recommendation}</Text>
            </View>
          )}

          {/* Raw Flow Telemetry */}
          <Text style={styles.flowTitle}>Network Flow Telemetry</Text>
          <View style={styles.telemetryGrid}>
            <View style={styles.telItem}><Text style={styles.telLabel}>Protocol</Text><Text style={styles.telVal}>{flow?.protocol_type?.toUpperCase()}</Text></View>
            <View style={styles.telItem}><Text style={styles.telLabel}>Service</Text><Text style={styles.telVal}>{flow?.service}</Text></View>
            <View style={styles.telItem}><Text style={styles.telLabel}>Flag</Text><Text style={styles.telVal}>{flow?.flag}</Text></View>
            <View style={styles.telItem}><Text style={styles.telLabel}>Src Bytes</Text><Text style={styles.telVal}>{flow?.src_bytes}</Text></View>
            <View style={styles.telItem}><Text style={styles.telLabel}>Dst Bytes</Text><Text style={styles.telVal}>{flow?.dst_bytes}</Text></View>
            <View style={styles.telItem}><Text style={styles.telLabel}>Anomaly MSE</Text><Text style={styles.telVal}>{pred?.anomaly_score?.toFixed(4)}</Text></View>
          </View>
        </View>
      ) : (
        <View style={styles.placeholderCard}>
          <Text style={styles.placeholderText}>Enable Live Stream above to begin ingesting network packets.</Text>
        </View>
      )}

      {/* Live Stream History Log */}
      <Text style={styles.sectionTitle}>Recent Ingested Flows</Text>
      {recentFeed.map((item, idx) => {
        const itemSev = item.prediction?.severity || 'LOW';
        const color = theme.severityColors[itemSev] || theme.colors.primary;
        return (
          <View key={idx} style={styles.historyRow}>
            <View style={[styles.historyDot, { backgroundColor: color }]} />
            <View style={styles.historyInfo}>
              <Text style={styles.historyType}>{item.prediction?.decision}</Text>
              <Text style={styles.historySub}>{item.flow_features?.protocol_type} • {item.flow_features?.service} • {item.flow_features?.src_bytes} bytes</Text>
            </View>
            <View style={styles.historyRight}>
              <Text style={[styles.historyScore, { color }]}>{item.prediction?.threat_score}</Text>
              <Text style={styles.historySev}>{itemSev}</Text>
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
  controlCard: {
    backgroundColor: theme.colors.card,
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    marginBottom: 20,
  },
  controlHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: 18, fontWeight: '800', color: theme.colors.text },
  subtitle: { fontSize: 13, color: theme.colors.textMuted, marginTop: 4 },
  switchWrapper: { alignItems: 'center' },
  statusText: { fontSize: 11, fontWeight: '800', marginBottom: 4 },
  card: {
    backgroundColor: theme.colors.card,
    borderRadius: 16,
    padding: 20,
    borderWidth: 1.5,
    marginBottom: 24,
  },
  badgeRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  badge: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  badgeText: { color: '#0A0E1A', fontWeight: '800', fontSize: 12 },
  recordIndex: { color: theme.colors.textMuted, fontSize: 13, fontWeight: '600' },
  scoreRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 16 },
  scoreBox: { flex: 1 },
  scoreLabel: { fontSize: 12, color: theme.colors.textMuted, fontWeight: '600' },
  scoreValue: { fontSize: 32, fontWeight: '900', marginTop: 4 },
  scoreMax: { fontSize: 14, color: theme.colors.textMuted, fontWeight: '500' },
  decisionValue: { fontSize: 18, fontWeight: '700', color: theme.colors.text, marginTop: 8 },
  alertBanner: {
    backgroundColor: 'rgba(255, 59, 86, 0.15)',
    borderLeftWidth: 4,
    borderLeftColor: theme.colors.danger,
    padding: 12,
    borderRadius: 8,
    marginVertical: 12,
  },
  alertTitle: { color: theme.colors.danger, fontWeight: '800', fontSize: 13, marginBottom: 4 },
  alertRec: { color: theme.colors.text, fontSize: 12, lineHeight: 18 },
  flowTitle: { fontSize: 13, fontWeight: '700', color: theme.colors.textMuted, marginTop: 8, marginBottom: 8 },
  telemetryGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
  telItem: { width: '31%', backgroundColor: theme.colors.surface, padding: 8, borderRadius: 8, marginBottom: 8 },
  telLabel: { fontSize: 10, color: theme.colors.textMuted },
  telVal: { fontSize: 12, fontWeight: '700', color: theme.colors.text, marginTop: 2 },
  placeholderCard: {
    backgroundColor: theme.colors.card,
    borderRadius: 16,
    padding: 30,
    alignItems: 'center',
    marginBottom: 24,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
  },
  placeholderText: { color: theme.colors.textMuted, textAlign: 'center', fontSize: 14 },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: theme.colors.text, marginBottom: 12 },
  historyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.card,
    padding: 14,
    borderRadius: 10,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
  },
  historyDot: { width: 10, height: 10, borderRadius: 5, marginRight: 12 },
  historyInfo: { flex: 1 },
  historyType: { color: theme.colors.text, fontWeight: '700', fontSize: 14 },
  historySub: { color: theme.colors.textMuted, fontSize: 11, marginTop: 2 },
  historyRight: { alignItems: 'flex-end' },
  historyScore: { fontSize: 16, fontWeight: '800' },
  historySev: { fontSize: 10, color: theme.colors.textMuted, fontWeight: '600' },
});
