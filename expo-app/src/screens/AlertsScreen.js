import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, RefreshControl } from 'react-native';
import { theme } from '../theme';
import { API_BASE_URL } from '../config';

export default function AlertsScreen() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState('ALL');
  const [expandedId, setExpandedId] = useState(null);

  const fetchAlerts = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/alerts?limit=50`);
      const data = await res.json();
      setAlerts(data.alerts || []);
    } catch (e) {
      console.log('Error fetching alerts:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const filteredAlerts = alerts.filter((a) => (filter === 'ALL' ? true : a.severity === filter));

  return (
    <View style={styles.container}>
      {/* Filter Tabs */}
      <View style={styles.filterRow}>
        {['ALL', 'CRITICAL', 'HIGH', 'MODERATE'].map((f) => (
          <TouchableOpacity
            key={f}
            style={[styles.filterBtn, filter === f && styles.filterBtnActive]}
            onPress={() => setFilter(f)}
          >
            <Text style={[styles.filterText, filter === f && styles.filterTextActive]}>{f}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Alerts List */}
      <ScrollView
        contentContainerStyle={styles.listContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchAlerts(); }} tintColor={theme.colors.primary} />}
      >
        {filteredAlerts.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyText}>No alerts found matching filter '{filter}'.</Text>
          </View>
        ) : (
          filteredAlerts.map((item) => {
            const isExpanded = expandedId === item.alert_id;
            const sevColor = theme.severityColors[item.severity] || theme.colors.primary;

            return (
              <TouchableOpacity
                key={item.alert_id}
                style={[styles.alertCard, { borderColor: sevColor }]}
                onPress={() => setExpandedId(isExpanded ? null : item.alert_id)}
                activeOpacity={0.8}
              >
                {/* Alert Top Row */}
                <View style={styles.alertHeader}>
                  <View style={styles.headerLeft}>
                    <View style={[styles.sevBadge, { backgroundColor: sevColor }]}>
                      <Text style={styles.sevBadgeText}>{item.severity}</Text>
                    </View>
                    <Text style={styles.alertId}>{item.alert_id}</Text>
                  </View>
                  <Text style={styles.timeText}>{item.timestamp}</Text>
                </View>

                {/* Main Alert Info */}
                <View style={styles.mainInfo}>
                  <Text style={styles.attackType}>{item.attack_type}</Text>
                  <Text style={[styles.threatScore, { color: sevColor }]}>
                    Score: {item.threat_score}
                  </Text>
                </View>

                {/* Quick Meta */}
                <View style={styles.metaRow}>
                  <Text style={styles.metaItem}>Confidence: <Text style={styles.metaVal}>{item.confidence}</Text></Text>
                  <Text style={styles.metaItem}>Anomaly MSE: <Text style={styles.metaVal}>{item.anomaly_score}</Text></Text>
                </View>

                {/* Expanded Details: XAI Reason & Recommendation */}
                {isExpanded && (
                  <View style={styles.expandedSection}>
                    <View style={styles.divider} />
                    <Text style={styles.xaiTitle}>🔍 Explainable AI (XAI) Attribution:</Text>
                    <Text style={styles.reasonText}>{item.reason || 'Attributed to statistical network flow deviation.'}</Text>

                    <Text style={styles.recTitle}>🛡️ Actionable Investigation Step:</Text>
                    <Text style={styles.recText}>{item.recommendation}</Text>
                  </View>
                )}
              </TouchableOpacity>
            );
          })
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.bg },
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: theme.colors.card,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.cardBorder,
    gap: 8,
  },
  filterBtn: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: theme.colors.surface,
  },
  filterBtnActive: { backgroundColor: theme.colors.primary },
  filterText: { color: theme.colors.textMuted, fontSize: 12, fontWeight: '700' },
  filterTextActive: { color: '#0A0E1A', fontWeight: '800' },
  listContent: { padding: 20, paddingBottom: 60 },
  alertCard: {
    backgroundColor: theme.colors.card,
    borderRadius: 14,
    padding: 16,
    borderWidth: 1.5,
    marginBottom: 14,
  },
  alertHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  sevBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6 },
  sevBadgeText: { color: '#0A0E1A', fontSize: 10, fontWeight: '900' },
  alertId: { color: theme.colors.textMuted, fontSize: 12, fontWeight: '600' },
  timeText: { color: theme.colors.textMuted, fontSize: 11 },
  mainInfo: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  attackType: { fontSize: 18, fontWeight: '800', color: theme.colors.text },
  threatScore: { fontSize: 16, fontWeight: '900' },
  metaRow: { flexDirection: 'row', gap: 16 },
  metaItem: { fontSize: 12, color: theme.colors.textMuted },
  metaVal: { color: theme.colors.text, fontWeight: '700' },
  divider: { height: 1, backgroundColor: theme.colors.cardBorder, marginVertical: 12 },
  expandedSection: { marginTop: 4 },
  xaiTitle: { fontSize: 13, fontWeight: '800', color: theme.colors.accent, marginBottom: 4 },
  reasonText: { color: theme.colors.text, fontSize: 12, lineHeight: 18, marginBottom: 12 },
  recTitle: { fontSize: 13, fontWeight: '800', color: theme.colors.primary, marginBottom: 4 },
  recText: { color: theme.colors.text, fontSize: 12, lineHeight: 18 },
  emptyCard: { backgroundColor: theme.colors.card, padding: 30, borderRadius: 12, alignItems: 'center', marginTop: 20 },
  emptyText: { color: theme.colors.textMuted, fontSize: 14 },
});
