"""
Enhanced SQLAlchemy models for Universal Battery Diagnostics Framework
Advanced schema supporting environmental monitoring, test scenarios, and analytics
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, BLOB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List
import json

Base = declarative_base()

class Battery(Base):
    """Core battery inventory model"""
    __tablename__ = 'batteries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    one_key_id = Column(String, unique=True)
    serial_number = Column(String)
    model = Column(String, nullable=False)
    manufacturer = Column(String, nullable=False)
    platform = Column(String)
    nominal_voltage_v = Column(Float, nullable=False)
    nominal_capacity_ah = Column(Float, nullable=False)
    chemistry = Column(String, default='Li-ion')
    cell_count = Column(Integer)
    cell_configuration = Column(String)
    manufacture_date = Column(DateTime)
    purchase_date = Column(DateTime)
    purchase_price = Column(Float)
    warranty_months = Column(Integer, default=36)
    initial_capacity_ah = Column(Float)
    first_use_date = Column(DateTime)
    location = Column(String)
    owner_notes = Column(Text)
    fleet_identifier = Column(String)
    is_active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    diagnostic_sessions = relationship("DiagnosticSession", back_populates="battery", cascade="all, delete-orphan")
    monitoring_sessions = relationship("MonitoringSession", back_populates="battery", cascade="all, delete-orphan")
    register_change_events = relationship("RegisterChangeEvent", back_populates="battery", cascade="all, delete-orphan")

class DiagnosticSession(Base):
    """Individual diagnostic session record"""
    __tablename__ = 'diagnostic_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    battery_id = Column(Integer, ForeignKey('batteries.id'), nullable=False)
    session_date = Column(DateTime, default=datetime.utcnow)
    session_type = Column(String, default='standard')
    protocol_version = Column(String)
    firmware_version = Column(String)
    hardware_interface = Column(String)
    operator = Column(String)
    session_duration_seconds = Column(Integer)
    data_completeness_percent = Column(Float)
    communication_errors = Column(Integer, default=0)
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String)
    environmental_notes = Column(Text)
    battery_state_before = Column(String)
    battery_state_after = Column(String)
    quality_rating = Column(Integer)
    notes = Column(Text)
    
    # Relationships
    battery = relationship("Battery", back_populates="diagnostic_sessions")
    raw_register_data = relationship("RawRegisterData", back_populates="session", cascade="all, delete-orphan")
    parsed_register_values = relationship("ParsedRegisterValue", back_populates="session", cascade="all, delete-orphan")
    health_metrics = relationship("HealthMetrics", back_populates="session", uselist=False, cascade="all, delete-orphan")
    cell_voltages = relationship("CellVoltage", back_populates="session", cascade="all, delete-orphan")
    discharge_histograms = relationship("DischargeHistogram", back_populates="session", cascade="all, delete-orphan")

class RawRegisterData(Base):
    """Raw register data as received from battery"""
    __tablename__ = 'raw_register_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('diagnostic_sessions.id'), nullable=False)
    register_address = Column(String, nullable=False)
    raw_value_hex = Column(String, nullable=False)
    raw_value_bytes = Column(BLOB)
    timestamp_ms = Column(Integer)
    checksum_valid = Column(Boolean)
    read_attempt = Column(Integer, default=1)
    protocol_notes = Column(Text)
    
    # Relationships
    session = relationship("DiagnosticSession", back_populates="raw_register_data")

class ParsedRegisterValue(Base):
    """Human-readable interpretations of register data"""
    __tablename__ = 'parsed_register_values'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('diagnostic_sessions.id'), nullable=False)
    register_address = Column(String, nullable=False)
    register_name = Column(String)
    parsed_value = Column(Float)
    parsed_value_text = Column(String)
    units = Column(String)
    data_type = Column(String)
    confidence_level = Column(String)
    parsing_method = Column(String)
    validation_status = Column(String)
    notes = Column(Text)
    
    # Relationships
    session = relationship("DiagnosticSession", back_populates="parsed_register_values")

class HealthMetrics(Base):
    """Calculated health metrics and battery analytics"""
    __tablename__ = 'health_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('diagnostic_sessions.id'), nullable=False)
    capacity_percentage = Column(Integer)
    health_score = Column(Integer)
    cycle_count = Column(Integer)
    internal_resistance_mohm = Column(Float)
    cell_imbalance_mv = Column(Integer)
    self_discharge_rate_percent = Column(Float)
    charge_efficiency_percent = Column(Float)
    discharge_efficiency_percent = Column(Float)
    temperature_during_test_c = Column(Float)
    voltage_sag_under_load_v = Column(Float)
    recovery_time_seconds = Column(Integer)
    power_capability_w = Column(Float)
    energy_density_wh_kg = Column(Float)
    predicted_remaining_cycles = Column(Integer)
    degradation_rate_percent_per_100cycles = Column(Float)
    thermal_stability_rating = Column(String)
    safety_status = Column(String)
    warranty_status = Column(String)
    calculated_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("DiagnosticSession", back_populates="health_metrics")

class CellVoltage(Base):
    """Individual cell voltage measurements"""
    __tablename__ = 'cell_voltages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('diagnostic_sessions.id'), nullable=False)
    cell_number = Column(Integer, nullable=False)
    voltage_mv = Column(Integer, nullable=False)
    voltage_rank = Column(Integer)
    deviation_from_average_mv = Column(Integer)
    is_lowest_cell = Column(Boolean, default=False)
    is_highest_cell = Column(Boolean, default=False)
    historical_consistency = Column(String)
    degradation_indicator = Column(Boolean, default=False)
    
    # Relationships
    session = relationship("DiagnosticSession", back_populates="cell_voltages")

class DischargeHistogram(Base):
    """Current usage pattern analysis"""
    __tablename__ = 'discharge_histograms'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('diagnostic_sessions.id'), nullable=False)
    current_range_start_a = Column(Float, nullable=False)
    current_range_end_a = Column(Float, nullable=False)
    time_spent_seconds = Column(Integer, nullable=False)
    percentage_of_total_use = Column(Float)
    cumulative_energy_wh = Column(Float)
    average_efficiency_percent = Column(Float)
    thermal_impact_rating = Column(String)
    stress_level = Column(String)
    real_world_equivalent = Column(String)
    
    # Relationships
    session = relationship("DiagnosticSession", back_populates="discharge_histograms")

class BatteryComparison(Base):
    """Battery performance comparisons and fleet analysis"""
    __tablename__ = 'battery_comparisons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    comparison_date = Column(DateTime, default=datetime.utcnow)
    comparison_type = Column(String, nullable=False)
    primary_battery_id = Column(Integer, ForeignKey('batteries.id'), nullable=False)
    reference_group = Column(String)
    sample_size = Column(Integer)
    primary_capacity_percentage = Column(Integer)
    reference_avg_capacity_percentage = Column(Float)
    capacity_percentile = Column(Integer)
    primary_health_score = Column(Integer)
    reference_avg_health_score = Column(Float)
    health_percentile = Column(Integer)
    primary_cycle_count = Column(Integer)
    reference_avg_cycle_count = Column(Float)
    cycle_percentile = Column(Integer)
    performance_category = Column(String)
    outlier_status = Column(String)
    statistical_confidence = Column(Float)
    actionable_insights = Column(Text)
    warranty_implications = Column(Text)

class CommunitySubmission(Base):
    """Anonymized community data for research"""
    __tablename__ = 'community_submissions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    submission_date = Column(DateTime, default=datetime.utcnow)
    battery_model = Column(String, nullable=False)
    battery_age_months = Column(Integer)
    cycle_count = Column(Integer)
    capacity_percentage = Column(Integer)
    health_score = Column(Integer)
    usage_pattern = Column(String)
    climate_zone = Column(String)
    storage_conditions = Column(String)
    submission_hash = Column(String, unique=True)
    data_quality_score = Column(Integer)
    validation_status = Column(String)
    contribution_value = Column(String)
    geographic_region = Column(String)
    user_consent_level = Column(String)

class MonitoringSession(Base):
    """Long-term battery monitoring sessions"""
    __tablename__ = 'monitoring_sessions'
    
    session_id = Column(String, primary_key=True)
    battery_id = Column(Integer, ForeignKey('batteries.id'), nullable=False)
    start_timestamp = Column(DateTime, nullable=False)
    end_timestamp = Column(DateTime)
    monitoring_type = Column(String, nullable=False)
    sample_interval_seconds = Column(Integer, nullable=False)
    total_samples = Column(Integer)
    monitoring_trigger = Column(String)
    monitoring_location = Column(String)
    environmental_controlled = Column(Boolean)
    data_completeness_percent = Column(Float)
    anomalies_detected = Column(Integer)
    session_quality = Column(String)
    insights_generated = Column(Text)
    follow_up_recommended = Column(Boolean, default=False)
    
    # Relationships
    battery = relationship("Battery", back_populates="monitoring_sessions")
    time_series_data = relationship("TimeSeriesData", back_populates="monitoring_session", cascade="all, delete-orphan")

class TimeSeriesData(Base):
    """Time-series monitoring data points"""
    __tablename__ = 'time_series_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    monitoring_session_id = Column(String, ForeignKey('monitoring_sessions.session_id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    voltage_mv = Column(Integer)
    current_ma = Column(Integer)
    temperature_c = Column(Float)
    state_of_charge_percent = Column(Integer)
    power_w = Column(Float)
    cumulative_energy_wh = Column(Float)
    event_marker = Column(String)
    data_quality = Column(String)
    
    # Relationships
    monitoring_session = relationship("MonitoringSession", back_populates="time_series_data")

class RegisterChangeEvent(Base):
    """Significant register changes over time"""
    __tablename__ = 'register_change_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    battery_id = Column(Integer, ForeignKey('batteries.id'), nullable=False)
    event_timestamp = Column(DateTime, default=datetime.utcnow)
    register_address = Column(String, nullable=False)
    previous_value = Column(String)
    new_value = Column(String, nullable=False)
    change_magnitude = Column(Float)
    change_type = Column(String)
    significance_level = Column(String)
    potential_causes = Column(Text)
    impact_assessment = Column(Text)
    recommendation = Column(Text)
    automated_detection = Column(Boolean, default=False)
    human_verified = Column(Boolean, default=False)
    follow_up_required = Column(Boolean, default=False)
    notes = Column(Text)
    
    # Relationships
    battery = relationship("Battery", back_populates="register_change_events")

# Utility functions for model operations
def create_battery_from_diagnostic(diagnostic_data: dict) -> Battery:
    """Create a new Battery record from diagnostic data"""
    return Battery(
        model=diagnostic_data.get('model'),
        manufacturer=diagnostic_data.get('manufacturer'),
        nominal_voltage_v=diagnostic_data.get('nominal_voltage_v'),
        nominal_capacity_ah=diagnostic_data.get('nominal_capacity_ah'),
        serial_number=diagnostic_data.get('serial_number'),
        one_key_id=diagnostic_data.get('one_key_id')
    )

def calculate_health_score(capacity_percentage: int, cycle_count: int, 
                          cell_imbalance_mv: int, internal_resistance_mohm: float) -> int:
    """Calculate overall battery health score from key metrics"""
    # Weighted scoring algorithm
    capacity_score = min(100, capacity_percentage * 1.2)  # Capacity is most important
    
    # Cycle count penalty (assume 1000 cycle life)
    cycle_penalty = min(25, (cycle_count / 1000) * 25)
    
    # Cell imbalance penalty
    imbalance_penalty = min(15, (cell_imbalance_mv / 100) * 15)
    
    # Resistance penalty (assume 200mOhm is concerning)
    resistance_penalty = min(10, (internal_resistance_mohm / 200) * 10)
    
    health_score = capacity_score - cycle_penalty - imbalance_penalty - resistance_penalty
    return max(0, min(100, int(health_score)))

def determine_warranty_status(battery: Battery, health_metrics: HealthMetrics) -> str:
    """Determine warranty status based on battery age and performance"""
    if not battery.purchase_date:
        return 'unknown'
    
    age_months = (datetime.utcnow() - battery.purchase_date).days / 30.4
    
    if age_months > battery.warranty_months:
        return 'expired'
    elif health_metrics.capacity_percentage < 60:
        return 'claim_eligible'
    elif health_metrics.capacity_percentage < 70:
        return 'monitor'
    else:
        return 'valid'