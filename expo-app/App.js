import React, { useState } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, SafeAreaView, StatusBar, Platform } from 'react-native';
import { theme } from './src/theme';
import OverviewScreen from './src/screens/OverviewScreen';
import LiveMonitorScreen from './src/screens/LiveMonitorScreen';
import AlertsScreen from './src/screens/AlertsScreen';
import ModelComparisonScreen from './src/screens/ModelComparisonScreen';
import AdaptiveLearningScreen from './src/screens/AdaptiveLearningScreen';

export default function App() {
  const [activeTab, setActiveTab] = useState('Overview');

  const renderScreen = () => {
    switch (activeTab) {
      case 'Overview':
        return <OverviewScreen onNavigate={setActiveTab} />;
      case 'Live':
        return <LiveMonitorScreen />;
      case 'Alerts':
        return <AlertsScreen />;
      case 'Metrics':
        return <ModelComparisonScreen />;
      case 'Adaptive':
        return <AdaptiveLearningScreen />;
      default:
        return <OverviewScreen onNavigate={setActiveTab} />;
    }
  };

  const tabs = [
    { id: 'Overview', label: 'Overview', icon: '🛡️' },
    { id: 'Live', label: 'Live Monitor', icon: '📡' },
    { id: 'Alerts', label: 'Alerts & XAI', icon: '🚨' },
    { id: 'Metrics', label: 'Benchmarks', icon: '📊' },
    { id: 'Adaptive', label: 'Adaptive AI', icon: '🧠' },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={theme.colors.bg} />
      
      {/* Top App Bar */}
      <View style={styles.topBar}>
        <View style={styles.brandRow}>
          <Text style={styles.brandIcon}>🛡️</Text>
          <View>
            <Text style={styles.brandTitle}>AEGIS<Text style={{ color: theme.colors.primary }}>IDS</Text></Text>
            <Text style={styles.brandSubtitle}>Deep Learning Intrusion Detection</Text>
          </View>
        </View>
        <View style={styles.liveTag}>
          <View style={styles.pulseDot} />
          <Text style={styles.liveTagText}>FASTAPI LINKED</Text>
        </View>
      </View>

      {/* Main View Area */}
      <View style={styles.mainContent}>
        {renderScreen()}
      </View>

      {/* Bottom Navigation Bar */}
      <View style={styles.navBar}>
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <TouchableOpacity
              key={tab.id}
              style={[styles.navItem, isActive && styles.navItemActive]}
              onPress={() => setActiveTab(tab.id)}
            >
              <Text style={styles.navIcon}>{tab.icon}</Text>
              <Text style={[styles.navLabel, isActive && styles.navLabelActive]}>{tab.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.bg,
    paddingTop: Platform.OS === 'android' ? 25 : 0,
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 14,
    backgroundColor: theme.colors.card,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.cardBorder,
  },
  brandRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  brandIcon: { fontSize: 24 },
  brandTitle: { fontSize: 18, fontWeight: '900', color: theme.colors.text, letterSpacing: 1 },
  brandSubtitle: { fontSize: 10, color: theme.colors.textMuted, fontWeight: '600' },
  liveTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 229, 153, 0.1)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: 'rgba(0, 229, 153, 0.3)',
  },
  pulseDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: theme.colors.primary, marginRight: 6 },
  liveTagText: { color: theme.colors.primary, fontSize: 9, fontWeight: '800', letterSpacing: 0.5 },
  mainContent: { flex: 1 },
  navBar: {
    flexDirection: 'row',
    backgroundColor: theme.colors.card,
    borderTopWidth: 1,
    borderTopColor: theme.colors.cardBorder,
    paddingVertical: 8,
    paddingHorizontal: 10,
    justifyContent: 'space-around',
  },
  navItem: {
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
  },
  navItemActive: {
    backgroundColor: theme.colors.surface,
  },
  navIcon: { fontSize: 18, marginBottom: 2 },
  navLabel: { fontSize: 11, fontWeight: '600', color: theme.colors.textMuted },
  navLabelActive: { color: theme.colors.primary, fontWeight: '800' },
});
