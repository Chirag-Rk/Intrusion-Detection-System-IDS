import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, RefreshControl } from 'react-native';
import { theme } from '../theme';
import { API_BASE_URL } from '../config';

export default function OverviewScreen({ onNavigate }) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/stats`);
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.log('Error fetching stats:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const stats = data?.stats || { total_analyzed: 0, normal_traffic: 0, malicious_detected: 0, critical_alerts: 0 };
  const severity = data?.severity_breakdown || { CRITICAL: 0, HIGH: 0, MODERATE: 0, LOW: 0 };

  return (
    <ScrollView 
      style={styles.container} 
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchStats(); }} tintColor={theme.colors.primary} />}
    >
      {/* Header Banner */}
      <View style={styles.headerCard}>
        <View style={styles.badgeRow}>
          <View style={styles.statusIndicator} />
          <Text style={styles.statusText}>ENGINE ACTIVE • REAL-TIME PROTECTION</Text>
        </View>
        <Text style={styles.title}>AegisIDS Security Console</Text>
        <Text style={styles.subtitle}>
          Adaptive and Explainable Deep Learning Intrusion Detection System
        </Text>
      </View>

      {/* KPI Cards Grid */}
      <Text style={styles.sectionTitle}>System Telemetry</Text>
      <View style={styles.grid}>
        <View style={styles.kpiCard}>
          <Text style={styles.kpiLabel}>Total Analyzed</Text>
          <Text style={styles.kpiValue}>{stats.total_analyzed}</Text>
          <Text style={styles.kpiSub}>Flow packets ingested</Text>
        </View>

        <View style={styles.kpiCard}>
          <Text style={styles.kpiLabel}>Normal Traffic</Text>
          <Text style={[styles.kpiValue, { color: theme.colors.primary }]}>{stats.normal_traffic}</Text>
          <Text style={styles.kpiSub}>Verified benign flows</Text>
        </View>

        <View style={styles.kpiCard}>
          <Text style={styles.kpiLabel}>Attacks Blocked</Text>
          <Text style={[styles.kpiValue, { color: theme.colors.danger }]}>{stats.malicious_detected}</Text>
          <Text style={styles.kpiSub}>Flagged intrusions</Text>
        </View>

        <View style={styles.kpiCard}>
          <Text style={styles.kpiLabel}>Critical Alerts</Text>
          <Text style={[styles.kpiValue, { color: theme.colors.danger }]}>{stats.critical_alerts}</Text>
          <Text style={styles.kpiSub}>Immediate action needed</Text>
        </View>
      </View>

      {/* Severity Breakdown */}
      <Text style={styles.sectionTitle}>Threat Severity Distribution</Text>
      <View style={styles.severityContainer}>
        {['CRITICAL', 'HIGH', 'MODERATE', 'LOW'].map((sev) => (
          <View key={sev} style={[styles.sevCard, { borderColor: theme.severityColors[sev] }]}>
            <Text style={[styles.sevCount, { color: theme.severityColors[sev] }]}>{severity[sev] || 0}</Text>
            <Text style={styles.sevLabel}>{sev}</Text>
          </View>
        ))}
      </View>

      {/* Quick Actions */}
      <Text style={styles.sectionTitle}>Quick Actions</Text>
      <View style={styles.actionRow}>
        <TouchableOpacity style={styles.primaryBtn} onPress={() => onNavigate('Live')}>
          <Text style={styles.btnText}>📡 Launch Live Monitor</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.secondaryBtn} onPress={() => onNavigate('Alerts')}>
          <Text style={styles.secBtnText}>🚨 View Active Alerts</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.bg },
  content: { padding: 20, paddingBottom: 60 },
  headerCard: {
    backgroundColor: theme.colors.card,
    borderRadius: 16,
    padding: 24,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    marginBottom: 24,
  },
  badgeRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  statusIndicator: { width: 8, height: 8, borderRadius: 4, backgroundColor: theme.colors.primary, marginRight: 8 },
  statusText: { color: theme.colors.primary, fontSize: 12, fontWeight: '700', letterSpacing: 1 },
  title: { fontSize: 24, fontWeight: '800', color: theme.colors.text, marginBottom: 6 },
  subtitle: { fontSize: 14, color: theme.colors.textMuted, lineHeight: 20 },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: theme.colors.text, marginBottom: 12, marginTop: 8 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', marginBottom: 20 },
  kpiCard: {
    width: '48%',
    backgroundColor: theme.colors.card,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    marginBottom: 12,
  },
  kpiLabel: { fontSize: 13, color: theme.colors.textMuted, fontWeight: '600' },
  kpiValue: { fontSize: 28, fontWeight: '800', color: theme.colors.text, marginVertical: 4 },
  kpiSub: { fontSize: 11, color: theme.colors.textMuted },
  severityContainer: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 24 },
  sevCard: {
    flex: 1,
    backgroundColor: theme.colors.card,
    padding: 14,
    borderRadius: 12,
    borderWidth: 1.5,
    marginHorizontal: 4,
    alignItems: 'center',
  },
  sevCount: { fontSize: 22, fontWeight: '800', marginBottom: 4 },
  sevLabel: { fontSize: 11, fontWeight: '700', color: theme.colors.textMuted },
  actionRow: { flexDirection: 'row', justifyContent: 'space-between', gap: 12 },
  primaryBtn: {
    flex: 1,
    backgroundColor: theme.colors.primary,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  btnText: { color: '#0A0E1A', fontWeight: '800', fontSize: 14 },
  secondaryBtn: {
    flex: 1,
    backgroundColor: theme.colors.surface,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  secBtnText: { color: theme.colors.text, fontWeight: '700', fontSize: 14 },
});
