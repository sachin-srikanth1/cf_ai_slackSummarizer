import React, { useEffect, useState } from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Box,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  TrendingUp,
  Assignment,
  Schedule,
  Sync,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/apiService';

interface DashboardStats {
  totalReports: number;
  lastSyncTime: string;
  nextScheduledReport: string;
  recentActivity: string[];
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual API calls
      const mockStats: DashboardStats = {
        totalReports: 12,
        lastSyncTime: new Date().toISOString(),
        nextScheduledReport: 'EOD - Today at 5:00 PM',
        recentActivity: [
          'Generated EOD report for #engineering',
          'Synced 45 new messages',
          'Updated preferences',
        ],
      };
      
      // Simulate API delay
      setTimeout(() => {
        setStats(mockStats);
        setLoading(false);
      }, 1000);
    } catch (err) {
      setError('Failed to load dashboard data');
      setLoading(false);
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      await apiService.syncSlackMessages();
      // Reload dashboard data after sync
      await loadDashboardData();
    } catch (err) {
      setError('Failed to sync messages');
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <Container>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* Quick Actions */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box display="flex" gap={2} flexWrap="wrap">
                <Button
                  variant="contained"
                  startIcon={<Assignment />}
                  onClick={() => navigate('/generate')}
                >
                  Generate EOD Report
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Assignment />}
                  onClick={() => navigate('/generate')}
                >
                  Generate EOW Report
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Sync />}
                  onClick={handleSync}
                  disabled={syncing}
                >
                  {syncing ? 'Syncing...' : 'Sync Messages'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Stats Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <TrendingUp sx={{ mr: 1, verticalAlign: 'middle' }} />
                Statistics
              </Typography>
              {stats && (
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Total Reports: {stats.totalReports}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Last Sync: {new Date(stats.lastSyncTime).toLocaleString()}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              {stats?.recentActivity.map((activity, index) => (
                <Typography key={index} variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  • {activity}
                </Typography>
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* Scheduled Reports */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <Schedule sx={{ mr: 1, verticalAlign: 'middle' }} />
                Scheduled Reports
              </Typography>
              {stats && (
                <Typography variant="body2" color="text.secondary">
                  Next: {stats.nextScheduledReport}
                </Typography>
              )}
              <Box mt={2}>
                <Button
                  size="small"
                  onClick={() => navigate('/settings')}
                >
                  Manage Schedule
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Reports */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Reports
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                No recent reports available. Generate your first report to get started!
              </Typography>
              <Button
                variant="outlined"
                onClick={() => navigate('/reports')}
              >
                View All Reports
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;