"""@bruin
name: export_dashboard_csv
depends:
  - mart_destination_scores
@bruin"""

from src.export_dashboard import export_destination_scores

export_destination_scores()
