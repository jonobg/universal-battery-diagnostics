"""
Advanced Battery Analytics Engine
Comprehensive battery analysis with predictive modeling and health assessment
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import sqlite3
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class BatteryHealthAssessment:
    """Comprehensive battery health assessment results"""
    battery_id: int
    overall_health_score: int
    capacity_percentage: int
    predicted_remaining_cycles: int
    degradation_rate: float
    risk_factors: List[str]
    maintenance_recommendations: List[str]
    warranty_status: str
    safety_concerns: List[str]
    performance_category: str
    confidence_score: float
    assessment_date: datetime

@dataclass
class FleetAnalytics:
    """Fleet-wide analytics and insights"""
    total_batteries: int
    average_health_score: float
    batteries_needing_attention: List[int]
    performance_outliers: List[int]
    cost_analysis: Dict[str, float]
    replacement_timeline: Dict[str, List[int]]
    optimization_opportunities: List[str]

class BatteryAnalyzer:
    """Advanced battery analytics engine with machine learning capabilities"""
    
    def __init__(self, database_path: str, config: Dict[str, Any] = None):
        self.database_path = database_path
        self.config = config or {}
        self.scaler = StandardScaler()
        self.degradation_model = None
        self.anomaly_detector = None
        self.model_trained = False
        
        # Health scoring weights
        self.health_weights = {
            'capacity': 0.40,
            'cycles': 0.25,
            'resistance': 0.15,
            'cell_balance': 0.10,
            'temperature': 0.10
        }
        
        # Performance thresholds
        self.thresholds = {
            'capacity_critical': 50,
            'capacity_warning': 70,
            'resistance_warning': 150,  # mOhm
            'resistance_critical': 300,
            'imbalance_warning': 30,    # mV
            'imbalance_critical': 60,
            'temperature_warning': 45,   # °C
            'temperature_critical': 55
        }

    def analyze_battery_health(self, battery_id: int) -> BatteryHealthAssessment:
        """Perform comprehensive battery health analysis"""
        logger.info(f"Starting health analysis for battery {battery_id}")
        
        # Get latest diagnostic data
        latest_data = self._get_latest_diagnostic_data(battery_id)
        if not latest_data:
            raise ValueError(f"No diagnostic data found for battery {battery_id}")
        
        # Calculate health metrics
        health_score = self._calculate_health_score(latest_data)
        degradation_rate = self._calculate_degradation_rate(battery_id)
        predicted_cycles = self._predict_remaining_cycles(battery_id)
        risk_factors = self._identify_risk_factors(latest_data)
        recommendations = self._generate_recommendations(latest_data, risk_factors)
        safety_concerns = self._assess_safety_concerns(latest_data)
        performance_category = self._categorize_performance(health_score, latest_data)
        
        return BatteryHealthAssessment(
            battery_id=battery_id,
            overall_health_score=health_score,
            capacity_percentage=latest_data.get('capacity_percentage', 0),
            predicted_remaining_cycles=predicted_cycles,
            degradation_rate=degradation_rate,
            risk_factors=risk_factors,
            maintenance_recommendations=recommendations,
            warranty_status=self._assess_warranty_status(battery_id, latest_data),
            safety_concerns=safety_concerns,
            performance_category=performance_category,
            confidence_score=self._calculate_confidence_score(latest_data),
            assessment_date=datetime.now()
        )

    def analyze_fleet_performance(self, fleet_ids: List[int] = None) -> FleetAnalytics:
        """Analyze performance across a fleet of batteries"""
        logger.info("Starting fleet performance analysis")
        
        # Get all active batteries if no specific fleet specified
        if fleet_ids is None:
            fleet_ids = self._get_all_active_batteries()
        
        health_scores = []
        batteries_needing_attention = []
        performance_outliers = []
        
        for battery_id in fleet_ids:
            try:
                assessment = self.analyze_battery_health(battery_id)
                health_scores.append(assessment.overall_health_score)
                
                if assessment.overall_health_score < 60 or assessment.safety_concerns:
                    batteries_needing_attention.append(battery_id)
                    
                if assessment.performance_category in ['outlier_high', 'outlier_low']:
                    performance_outliers.append(battery_id)
                    
            except Exception as e:
                logger.warning(f"Failed to analyze battery {battery_id}: {e}")
        
        # Calculate fleet metrics
        avg_health = np.mean(health_scores) if health_scores else 0
        cost_analysis = self._calculate_fleet_costs(fleet_ids)
        replacement_timeline = self._predict_replacement_timeline(fleet_ids)
        optimization_opportunities = self._identify_optimization_opportunities(fleet_ids)
        
        return FleetAnalytics(
            total_batteries=len(fleet_ids),
            average_health_score=avg_health,
            batteries_needing_attention=batteries_needing_attention,
            performance_outliers=performance_outliers,
            cost_analysis=cost_analysis,
            replacement_timeline=replacement_timeline,
            optimization_opportunities=optimization_opportunities
        )

    def train_predictive_models(self, min_samples: int = 50) -> bool:
        """Train machine learning models for degradation prediction"""
        logger.info("Training predictive models")
        
        try:
            # Get training data
            training_data = self._prepare_training_data()
            if len(training_data) < min_samples:
                logger.warning(f"Insufficient data for training: {len(training_data)} < {min_samples}")
                return False
            
            # Prepare features and targets
            features = training_data[['cycle_count', 'age_days', 'avg_temperature', 
                                    'usage_intensity', 'cell_imbalance_mv']].fillna(0)
            target_capacity = training_data['capacity_percentage'].fillna(0)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, target_capacity, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train degradation model
            self.degradation_model = RandomForestRegressor(
                n_estimators=100, random_state=42, max_depth=10
            )
            self.degradation_model.fit(X_train_scaled, y_train)
            
            # Train anomaly detection model
            self.anomaly_detector = IsolationForest(
                contamination=0.1, random_state=42
            )
            self.anomaly_detector.fit(X_train_scaled)
            
            # Evaluate models
            y_pred = self.degradation_model.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            logger.info(f"Model trained - MAE: {mae:.2f}, R²: {r2:.3f}")
            self.model_trained = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to train models: {e}")
            return False

    def detect_anomalies(self, battery_id: int) -> Dict[str, Any]:
        """Detect anomalies in battery behavior"""
        if not self.model_trained:
            logger.warning("Models not trained, using rule-based anomaly detection")
            return self._rule_based_anomaly_detection(battery_id)
        
        latest_data = self._get_latest_diagnostic_data(battery_id)
        if not latest_data:
            return {'anomalies': [], 'confidence': 0.0}
        
        # Prepare features
        features = np.array([[
            latest_data.get('cycle_count', 0),
            latest_data.get('age_days', 0),
            latest_data.get('temperature_during_test_c', 25),
            latest_data.get('usage_intensity', 1.0),
            latest_data.get('cell_imbalance_mv', 0)
        ]])
        
        features_scaled = self.scaler.transform(features)
        
        # Detect anomalies
        anomaly_score = self.anomaly_detector.decision_function(features_scaled)[0]
        is_anomaly = self.anomaly_detector.predict(features_scaled)[0] == -1
        
        anomalies = []
        if is_anomaly:
            anomalies = self._classify_anomaly_type(latest_data)
        
        return {
            'anomalies': anomalies,
            'anomaly_score': anomaly_score,
            'is_anomaly': is_anomaly,
            'confidence': abs(anomaly_score)
        }

    def _calculate_health_score(self, data: Dict[str, Any]) -> int:
        """Calculate weighted health score from multiple metrics"""
        scores = {}
        
        # Capacity score (0-100)
        capacity_pct = data.get('capacity_percentage', 0)
        scores['capacity'] = min(100, max(0, capacity_pct))
        
        # Cycle count score (assumes 1000 cycle life)
        cycle_count = data.get('cycle_count', 0)
        cycle_life_remaining = max(0, 1000 - cycle_count) / 1000
        scores['cycles'] = cycle_life_remaining * 100
        
        # Resistance score
        resistance = data.get('internal_resistance_mohm', 0)
        if resistance <= 100:
            scores['resistance'] = 100
        elif resistance <= 200:
            scores['resistance'] = 100 - ((resistance - 100) / 100) * 50
        else:
            scores['resistance'] = max(0, 50 - ((resistance - 200) / 100) * 50)
        
        # Cell balance score
        imbalance = data.get('cell_imbalance_mv', 0)
        if imbalance <= 20:
            scores['cell_balance'] = 100
        elif imbalance <= 50:
            scores['cell_balance'] = 100 - ((imbalance - 20) / 30) * 50
        else:
            scores['cell_balance'] = max(0, 50 - ((imbalance - 50) / 50) * 50)
        
        # Temperature performance score
        temperature = data.get('temperature_during_test_c', 25)
        if temperature <= 35:
            scores['temperature'] = 100
        elif temperature <= 50:
            scores['temperature'] = 100 - ((temperature - 35) / 15) * 30
        else:
            scores['temperature'] = max(0, 70 - ((temperature - 50) / 10) * 70)
        
        # Calculate weighted average
        weighted_score = sum(
            scores[metric] * self.health_weights[metric] 
            for metric in scores
        )
        
        return max(0, min(100, int(weighted_score)))

    def _calculate_degradation_rate(self, battery_id: int) -> float:
        """Calculate capacity degradation rate per 100 cycles"""
        with sqlite3.connect(self.database_path) as conn:
            query = """
            SELECT hm.capacity_percentage, hm.cycle_count, ds.session_date
            FROM health_metrics hm
            JOIN diagnostic_sessions ds ON hm.session_id = ds.id
            WHERE ds.battery_id = ? AND ds.success = 1
            ORDER BY ds.session_date
            """
            df = pd.read_sql_query(query, conn, params=(battery_id,))
        
        if len(df) < 2:
            return 0.0
        
        # Calculate linear regression slope
        x = df['cycle_count'].values
        y = df['capacity_percentage'].values
        
        if len(x) < 2 or np.std(x) == 0:
            return 0.0
        
        slope = np.polyfit(x, y, 1)[0]  # % per cycle
        return abs(slope * 100)  # % per 100 cycles

    def _predict_remaining_cycles(self, battery_id: int) -> int:
        """Predict remaining useful cycles"""
        latest_data = self._get_latest_diagnostic_data(battery_id)
        if not latest_data:
            return 0
        
        current_capacity = latest_data.get('capacity_percentage', 0)
        degradation_rate = self._calculate_degradation_rate(battery_id)
        
        if degradation_rate <= 0:
            return 500  # Default estimate if no degradation data
        
        # Predict cycles until 50% capacity (end of life)
        remaining_capacity = current_capacity - 50
        cycles_remaining = (remaining_capacity / degradation_rate) * 100
        
        return max(0, int(cycles_remaining))

    def _identify_risk_factors(self, data: Dict[str, Any]) -> List[str]:
        """Identify potential risk factors affecting battery health"""
        risks = []
        
        if data.get('capacity_percentage', 100) < self.thresholds['capacity_warning']:
            risks.append('Low capacity')
        
        if data.get('internal_resistance_mohm', 0) > self.thresholds['resistance_warning']:
            risks.append('High internal resistance')
        
        if data.get('cell_imbalance_mv', 0) > self.thresholds['imbalance_warning']:
            risks.append('Cell imbalance')
        
        if data.get('temperature_during_test_c', 25) > self.thresholds['temperature_warning']:
            risks.append('High operating temperature')
        
        if data.get('cycle_count', 0) > 800:
            risks.append('High cycle count')
        
        # Check for rapid degradation
        degradation_rate = self._calculate_degradation_rate(data.get('battery_id', 0))
        if degradation_rate > 2.0:  # >2% per 100 cycles
            risks.append('Rapid capacity degradation')
        
        return risks

    def _generate_recommendations(self, data: Dict[str, Any], risk_factors: List[str]) -> List[str]:
        """Generate maintenance and usage recommendations"""
        recommendations = []
        
        if 'Low capacity' in risk_factors:
            recommendations.append('Consider battery replacement or capacity testing')
        
        if 'High internal resistance' in risk_factors:
            recommendations.append('Avoid high-current applications; check connections')
        
        if 'Cell imbalance' in risk_factors:
            recommendations.append('Perform cell balancing; avoid deep discharge')
        
        if 'High operating temperature' in risk_factors:
            recommendations.append('Improve ventilation; avoid continuous high loads')
        
        if 'High cycle count' in risk_factors:
            recommendations.append('Plan for replacement; increase monitoring frequency')
        
        if 'Rapid capacity degradation' in risk_factors:
            recommendations.append('Investigate usage patterns; check charger compatibility')
        
        # General recommendations
        if data.get('capacity_percentage', 100) > 80:
            recommendations.append('Battery in good condition; continue normal use')
        else:
            recommendations.append('Increase diagnostic frequency to monthly')
        
        return recommendations

    def _assess_safety_concerns(self, data: Dict[str, Any]) -> List[str]:
        """Assess potential safety concerns"""
        concerns = []
        
        if data.get('capacity_percentage', 100) < self.thresholds['capacity_critical']:
            concerns.append('Critical capacity loss - replacement recommended')
        
        if data.get('internal_resistance_mohm', 0) > self.thresholds['resistance_critical']:
            concerns.append('Excessive internal resistance - fire/thermal risk')
        
        if data.get('cell_imbalance_mv', 0) > self.thresholds['imbalance_critical']:
            concerns.append('Severe cell imbalance - potential cell failure')
        
        if data.get('temperature_during_test_c', 25) > self.thresholds['temperature_critical']:
            concerns.append('Overheating detected - thermal runaway risk')
        
        return concerns

    def _categorize_performance(self, health_score: int, data: Dict[str, Any]) -> str:
        """Categorize battery performance relative to peers"""
        if health_score >= 90:
            return 'excellent'
        elif health_score >= 75:
            return 'good'
        elif health_score >= 60:
            return 'fair'
        elif health_score >= 40:
            return 'poor'
        else:
            return 'critical'

    def _assess_warranty_status(self, battery_id: int, data: Dict[str, Any]) -> str:
        """Assess warranty status and claim eligibility"""
        with sqlite3.connect(self.database_path) as conn:
            query = """
            SELECT purchase_date, warranty_months 
            FROM batteries 
            WHERE id = ?
            """
            result = conn.execute(query, (battery_id,)).fetchone()
        
        if not result or not result[0]:
            return 'unknown'
        
        purchase_date = datetime.fromisoformat(result[0])
        warranty_months = result[1] or 36
        
        age_months = (datetime.now() - purchase_date).days / 30.4
        
        if age_months > warranty_months:
            return 'expired'
        elif data.get('capacity_percentage', 100) < 60:
            return 'claim_eligible'
        elif data.get('capacity_percentage', 100) < 70:
            return 'monitor'
        else:
            return 'valid'

    def _calculate_confidence_score(self, data: Dict[str, Any]) -> float:
        """Calculate confidence in the assessment"""
        confidence_factors = []
        
        # Data completeness
        expected_fields = ['capacity_percentage', 'cycle_count', 'internal_resistance_mohm', 
                          'cell_imbalance_mv', 'temperature_during_test_c']
        completeness = sum(1 for field in expected_fields if data.get(field) is not None) / len(expected_fields)
        confidence_factors.append(completeness)
        
        # Data quality rating
        quality_rating = data.get('quality_rating', 3) / 5.0
        confidence_factors.append(quality_rating)
        
        # Model training status
        model_confidence = 0.9 if self.model_trained else 0.7
        confidence_factors.append(model_confidence)
        
        return np.mean(confidence_factors)

    def _get_latest_diagnostic_data(self, battery_id: int) -> Optional[Dict[str, Any]]:
        """Get the most recent diagnostic data for a battery"""
        with sqlite3.connect(self.database_path) as conn:
            query = """
            SELECT 
                ds.battery_id,
                ds.session_date,
                ds.quality_rating,
                hm.capacity_percentage,
                hm.cycle_count,
                hm.internal_resistance_mohm,
                hm.cell_imbalance_mv,
                hm.temperature_during_test_c,
                b.purchase_date,
                julianday('now') - julianday(b.purchase_date) as age_days
            FROM diagnostic_sessions ds
            JOIN health_metrics hm ON ds.id = hm.session_id
            JOIN batteries b ON ds.battery_id = b.id
            WHERE ds.battery_id = ? AND ds.success = 1
            ORDER BY ds.session_date DESC
            LIMIT 1
            """
            result = conn.execute(query, (battery_id,)).fetchone()
        
        if not result:
            return None
        
        columns = ['battery_id', 'session_date', 'quality_rating', 'capacity_percentage',
                  'cycle_count', 'internal_resistance_mohm', 'cell_imbalance_mv',
                  'temperature_during_test_c', 'purchase_date', 'age_days']
        
        return dict(zip(columns, result))

    def _get_all_active_batteries(self) -> List[int]:
        """Get list of all active battery IDs"""
        with sqlite3.connect(self.database_path) as conn:
            query = "SELECT id FROM batteries WHERE is_active = 1"
            results = conn.execute(query).fetchall()
        
        return [row[0] for row in results]

    def _prepare_training_data(self) -> pd.DataFrame:
        """Prepare training data for machine learning models"""
        with sqlite3.connect(self.database_path) as conn:
            query = """
            SELECT 
                hm.capacity_percentage,
                hm.cycle_count,
                hm.internal_resistance_mohm,
                hm.cell_imbalance_mv,
                hm.temperature_during_test_c as avg_temperature,
                julianday('now') - julianday(b.purchase_date) as age_days,
                CASE 
                    WHEN dh.total_high_current > 0 THEN dh.total_high_current / dh.total_usage
                    ELSE 1.0 
                END as usage_intensity
            FROM health_metrics hm
            JOIN diagnostic_sessions ds ON hm.session_id = ds.id
            JOIN batteries b ON ds.battery_id = b.id
            LEFT JOIN (
                SELECT 
                    session_id,
                    SUM(time_spent_seconds) as total_usage,
                    SUM(CASE WHEN current_range_start_a > 20 THEN time_spent_seconds ELSE 0 END) as total_high_current
                FROM discharge_histograms
                GROUP BY session_id
            ) dh ON ds.id = dh.session_id
            WHERE ds.success = 1
            """
            return pd.read_sql_query(query, conn)

    def _rule_based_anomaly_detection(self, battery_id: int) -> Dict[str, Any]:
        """Rule-based anomaly detection when ML models are not available"""
        latest_data = self._get_latest_diagnostic_data(battery_id)
        if not latest_data:
            return {'anomalies': [], 'confidence': 0.0}
        
        anomalies = []
        
        # Check for sudden capacity drop
        if latest_data.get('capacity_percentage', 100) < 70:
            anomalies.append('Low capacity detected')
        
        # Check for high resistance
        if latest_data.get('internal_resistance_mohm', 0) > 200:
            anomalies.append('High internal resistance')
        
        # Check for cell imbalance
        if latest_data.get('cell_imbalance_mv', 0) > 50:
            anomalies.append('Significant cell imbalance')
        
        return {
            'anomalies': anomalies,
            'confidence': 0.7,
            'method': 'rule_based'
        }

    def _classify_anomaly_type(self, data: Dict[str, Any]) -> List[str]:
        """Classify the type of anomaly detected"""
        anomalies = []
        
        if data.get('capacity_percentage', 100) < 60:
            anomalies.append('Capacity anomaly')
        
        if data.get('internal_resistance_mohm', 0) > 300:
            anomalies.append('Resistance anomaly')
        
        if data.get('cell_imbalance_mv', 0) > 100:
            anomalies.append('Cell balance anomaly')
        
        if data.get('temperature_during_test_c', 25) > 60:
            anomalies.append('Temperature anomaly')
        
        return anomalies

    def _calculate_fleet_costs(self, fleet_ids: List[int]) -> Dict[str, float]:
        """Calculate fleet cost analysis"""
        # Placeholder for cost calculation logic
        return {
            'total_investment': 0.0,
            'maintenance_costs': 0.0,
            'replacement_costs': 0.0,
            'productivity_impact': 0.0
        }

    def _predict_replacement_timeline(self, fleet_ids: List[int]) -> Dict[str, List[int]]:
        """Predict when batteries will need replacement"""
        timeline = {
            'immediate': [],    # Replace within 30 days
            'short_term': [],   # Replace within 3 months
            'medium_term': [],  # Replace within 6 months
            'long_term': []     # Replace within 12 months
        }
        
        for battery_id in fleet_ids:
            try:
                assessment = self.analyze_battery_health(battery_id)
                
                if assessment.overall_health_score < 40:
                    timeline['immediate'].append(battery_id)
                elif assessment.overall_health_score < 60:
                    timeline['short_term'].append(battery_id)
                elif assessment.overall_health_score < 75:
                    timeline['medium_term'].append(battery_id)
                else:
                    timeline['long_term'].append(battery_id)
                    
            except Exception as e:
                logger.warning(f"Failed to assess battery {battery_id}: {e}")
        
        return timeline

    def _identify_optimization_opportunities(self, fleet_ids: List[int]) -> List[str]:
        """Identify fleet optimization opportunities"""
        opportunities = []
        
        # Analyze fleet for patterns
        health_assessments = []
        for battery_id in fleet_ids:
            try:
                assessment = self.analyze_battery_health(battery_id)
                health_assessments.append(assessment)
            except Exception:
                continue
        
        if not health_assessments:
            return opportunities
        
        # Check for common issues
        low_health_count = sum(1 for a in health_assessments if a.overall_health_score < 70)
        if low_health_count > len(health_assessments) * 0.3:
            opportunities.append('High percentage of batteries with poor health - review usage patterns')
        
        # Check for safety concerns
        safety_issues = sum(1 for a in health_assessments if a.safety_concerns)
        if safety_issues > 0:
            opportunities.append(f'{safety_issues} batteries have safety concerns - immediate attention required')
        
        # Check for warranty claims
        warranty_eligible = sum(1 for a in health_assessments if 'claim' in a.warranty_status.lower())
        if warranty_eligible > 0:
            opportunities.append(f'{warranty_eligible} batteries may be eligible for warranty claims')
        
        return opportunities