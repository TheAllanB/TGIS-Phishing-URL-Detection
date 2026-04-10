import pandas as pd
import numpy as np
import joblib
import os
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Optional
from src.core.logger import log

class DataPreprocessor:
    """
    Handles feature imputation and scaling for the ML pipeline.
    """
    
    def __init__(self):
        self.imputer = SimpleImputer(strategy='constant', fill_value=-1)
        self.scaler = StandardScaler()
        self.is_fitted = False

    def fit_transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Fit the preprocessor on X and return transformed data.

        Args:
            X (pd.DataFrame): Input features.

        Returns:
            np.ndarray: Imputed and scaled features.
        """
        log.info(f"Preprocessing {X.shape[1]} features for {X.shape[0]} samples...")

        # Cast to float64 so the imputer's fill_value dtype always matches
        X = X.apply(pd.to_numeric, errors='coerce').astype(np.float64)

        # 1. Impute missing values (e.g., failed WHOIS/Content scrapes)
        X_imputed = self.imputer.fit_transform(X)
        
        # 2. Scale features (StandardScaler)
        X_scaled = self.scaler.fit_transform(X_imputed)
        
        self.is_fitted = True
        log.success("Data preprocessing completed (Fit & Transform).")
        return X_scaled

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform data using the already fitted preprocessor."""
        if not self.is_fitted:
            log.error("Preprocessor not fitted. Call fit_transform first.")
            return None

        # Cast to float64 so dtype matches what the imputer was fit on.
        # Non-numeric values (None, strings) become NaN, then imputed with fill_value=-1.
        X = X.apply(pd.to_numeric, errors='coerce').astype(np.float64)

        X_imputed = self.imputer.transform(X)
        X_scaled = self.scaler.transform(X_imputed)
        return X_scaled

    def save(self, directory: str):
        """Persistent storage for the fitted models."""
        if not self.is_fitted:
            log.warning("Saving an unfitted preprocessor.")
            
        try:
            os.makedirs(directory, exist_ok=True)
            joblib.dump(self.imputer, os.path.join(directory, 'imputer.joblib'))
            joblib.dump(self.scaler, os.path.join(directory, 'scaler.joblib'))
            log.info(f"Preprocessor models saved to {directory}")
        except Exception as e:
            log.error(f"Failed to save preprocessor: {e}")

    def load(self, directory: str):
        """Load fitted models from a directory."""
        try:
            self.imputer = joblib.load(os.path.join(directory, 'imputer.joblib'))
            self.scaler = joblib.load(os.path.join(directory, 'scaler.joblib'))

            # Patch cross-version dtype incompatibility (models saved with sklearn 1.8.0,
            # loaded under sklearn 1.5.x).  The imputer's internal `statistics_` array
            # may be stored as dtype('O'), which sklearn 1.5.x rejects during transform.
            if hasattr(self.imputer, 'statistics_') and self.imputer.statistics_ is not None:
                self.imputer.statistics_ = np.array(self.imputer.statistics_, dtype=np.float64)
            if hasattr(self.imputer, 'fill_value') and self.imputer.fill_value is not None:
                try:
                    self.imputer.fill_value = float(self.imputer.fill_value)
                except (TypeError, ValueError):
                    self.imputer.fill_value = -1.0

            self.is_fitted = True
            log.info(f"Preprocessor models loaded from {directory}")
        except Exception as e:
            log.error(f"Failed to load preprocessor models: {e}")
            self.is_fitted = False
