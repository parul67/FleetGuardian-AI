import os
import random
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from app.core.config import settings

def generate_synthetic_dataset(num_samples: int = 1500) -> str:
    """Generates a synthetic dataset for driver risk classification."""
    settings.create_dirs()
    dataset_path = os.path.join(settings.DATASET_DIR, "synthetic_driver_data.csv")
    
    data = []
    for i in range(num_samples):
        driver_id = random.randint(101, 150)
        vehicle_id = random.randint(201, 250)
        
        # Draw features
        drowsiness_score = round(random.uniform(0.0, 1.0), 3)
        phone_usage_frequency = round(random.uniform(0.0, 1.0), 3)
        seatbelt_present = random.choice([True, True, True, True, False]) # 20% infraction rate
        lane_departure_count = random.randint(0, 8)
        speed = round(random.uniform(30.0, 110.0), 2)
        distraction_score = round(random.uniform(0.0, 1.0), 3)
        
        # Environment factors
        weather = random.choice(["clear", "rainy", "snowy", "foggy"])
        time_of_day = random.choice(["day", "night", "dusk"])
        alert_count = random.randint(0, 10)

        # Risk Heuristic logic to assign ground truth targets (0=Low, 1=Medium, 2=High, 3=Critical)
        score = 0
        if drowsiness_score > 0.6 or phone_usage_frequency > 0.5:
            score += 4
        elif drowsiness_score > 0.3 or phone_usage_frequency > 0.15:
            score += 2
            
        if not seatbelt_present:
            score += 2
        if lane_departure_count > 3 or speed > 85.0:
            score += 3
        elif lane_departure_count > 1 or speed > 70.0:
            score += 1
        if distraction_score > 0.4:
            score += 2
            
        if weather in ["rainy", "foggy"] or time_of_day == "night":
            score += 1

        if score >= 7:
            risk_level = 3  # Critical
        elif score >= 4:
            risk_level = 2  # High
        elif score >= 2:
            risk_level = 1  # Medium
        else:
            risk_level = 0  # Low

        data.append({
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "drowsiness_score": drowsiness_score,
            "phone_usage_frequency": phone_usage_frequency,
            "seatbelt_present": 1 if seatbelt_present else 0,
            "lane_departure_count": lane_departure_count,
            "speed": speed,
            "distraction_score": distraction_score,
            "weather": weather,
            "time_of_day": time_of_day,
            "alert_count": alert_count,
            "risk_level": risk_level
        })
        
    df = pd.DataFrame(data)
    df.to_csv(dataset_path, index=False)
    print(f"Generated synthetic dataset with {num_samples} records at: {dataset_path}")
    return dataset_path

def train_model():
    """Trains the Random Forest model and saves it as pkl."""
    dataset_path = os.path.join(settings.DATASET_DIR, "synthetic_driver_data.csv")
    if not os.path.exists(dataset_path):
        dataset_path = generate_synthetic_dataset()
        
    df = pd.read_csv(dataset_path)
    
    # Feature columns (numerical inputs only for model ease)
    feature_cols = [
        "drowsiness_score",
        "phone_usage_frequency",
        "seatbelt_present",
        "lane_departure_count",
        "speed",
        "distraction_score"
    ]
    
    X = df[feature_cols]
    y = df["risk_level"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Classifier
    clf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    clf.fit(X_train, y_train)
    
    # Eval
    preds = clf.predict(X_test)
    accuracy = accuracy_score(y_test, preds)
    print("--------------------------------------------------")
    print(f"Random Forest Training Completed.")
    print(f"Test Accuracy: {accuracy:.4f}")
    print("--------------------------------------------------")
    print("Classification Report:")
    print(classification_report(y_test, preds, target_names=["Low", "Medium", "High", "Critical"]))
    
    # Save model
    model_path = os.path.join(settings.MODEL_DIR, "risk_predictor.pkl")
    joblib.dump(clf, model_path)
    print(f"Serialized model saved to: {model_path}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    train_model()
