import React, { useEffect, useState } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Chip,
  Box,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
} from '@mui/material';
import {
  Download,
  Refresh,
  Assignment,
  Description,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { apiService, ReportMetadata } from '../services/apiService';

const Reports: React.FC = () => {
  const [reports, setReports] = useState<ReportMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      setLoading(true);
      setError(null);
      const reportsData = await apiService.getReports();
      setReports(reportsData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (reportId: string, reportType: string) => {
    try {
      setDownloading(reportId);
      const blob = await apiService.downloadReport(reportId);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportType}_summary_${reportId}.pdf`;
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to download report');
    } finally {
      setDownloading(null);
    }
  };

  const getTypeIcon = (type: string) => {
    return type === 'EOD' ? <Description /> : <Assignment />;
  };

  const getTypeColor = (type: string): 'primary' | 'secondary' => {
    return type === 'EOD' ? 'primary' : 'secondary';
  };

  if (loading) {
    return (
      <Container>
        <Box display=\"flex\" justifyContent=\"center\" alignItems=\"center\" minHeight=\"400px\">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth=\"lg\" sx={{ mt: 4, mb: 4 }}>
      <Box display=\"flex\" justifyContent=\"space-between\" alignItems=\"center\" mb={3}>
        <Typography variant=\"h4\" component=\"h1\">
          Reports
        </Typography>
        <Button
          variant=\"outlined\"
          startIcon={<Refresh />}
          onClick={loadReports}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity=\"error\" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {reports.length === 0 ? (
        <Card>
          <CardContent>
            <Box textAlign=\"center\" py={4}>
              <Assignment sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant=\"h6\" color=\"text.secondary\" gutterBottom>
                No Reports Generated Yet
              </Typography>
              <Typography variant=\"body2\" color=\"text.secondary\" mb={3}>
                Generate your first EOD or EOW summary to see reports here.
              </Typography>
              <Button variant=\"contained\" href=\"/generate\">
                Generate Report
              </Button>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent>
            <Typography variant=\"h6\" gutterBottom>
              Generated Reports ({reports.length})
            </Typography>
            
            <TableContainer component={Paper} variant=\"outlined\">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Generated</TableCell>
                    <TableCell>Messages</TableCell>
                    <TableCell>Channels</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {reports.map((report) => (
                    <TableRow key={report.id} hover>
                      <TableCell>
                        <Box display=\"flex\" alignItems=\"center\">
                          {getTypeIcon(report.type)}
                          <Chip
                            label={report.type}
                            color={getTypeColor(report.type)}
                            size=\"small\"
                            sx={{ ml: 1 }}
                          />
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Typography variant=\"body2\">
                          {format(new Date(report.generated_at), 'MMM dd, yyyy')}
                        </Typography>
                        <Typography variant=\"caption\" color=\"text.secondary\">
                          {format(new Date(report.generated_at), 'HH:mm')}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Typography variant=\"body2\">
                          {report.message_count} messages
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Box>
                          {report.channels.length > 0 ? (
                            <Box>
                              {report.channels.slice(0, 2).map((channel) => (
                                <Chip
                                  key={channel}
                                  label={`#${channel}`}
                                  size=\"small\"
                                  variant=\"outlined\"
                                  sx={{ mr: 0.5, mb: 0.5 }}
                                />
                              ))}\n                              {report.channels.length > 2 && (\n                                <Typography variant=\"caption\" color=\"text.secondary\">\n                                  +{report.channels.length - 2} more\n                                </Typography>\n                              )}\n                            </Box>\n                          ) : (\n                            <Typography variant=\"body2\" color=\"text.secondary\">\n                              All channels\n                            </Typography>\n                          )}\n                        </Box>\n                      </TableCell>\n                      \n                      <TableCell>\n                        <IconButton\n                          onClick={() => handleDownload(report.id, report.type)}\n                          disabled={!report.pdf_available || downloading === report.id}\n                          color=\"primary\"\n                        >\n                          {downloading === report.id ? (\n                            <CircularProgress size={20} />\n                          ) : (\n                            <Download />\n                          )}\n                        </IconButton>\n                      </TableCell>\n                    </TableRow>\n                  ))}\n                </TableBody>\n              </Table>\n            </TableContainer>\n          </CardContent>\n        </Card>\n      )}\n\n      {/* Summary Statistics */}\n      {reports.length > 0 && (\n        <Grid container spacing={3} sx={{ mt: 3 }}>\n          <Grid item xs={12} sm={6} md={3}>\n            <Card>\n              <CardContent>\n                <Typography variant=\"h6\" color=\"primary\">\n                  {reports.length}\n                </Typography>\n                <Typography variant=\"body2\" color=\"text.secondary\">\n                  Total Reports\n                </Typography>\n              </CardContent>\n            </Card>\n          </Grid>\n          \n          <Grid item xs={12} sm={6} md={3}>\n            <Card>\n              <CardContent>\n                <Typography variant=\"h6\" color=\"primary\">\n                  {reports.filter(r => r.type === 'EOD').length}\n                </Typography>\n                <Typography variant=\"body2\" color=\"text.secondary\">\n                  EOD Reports\n                </Typography>\n              </CardContent>\n            </Card>\n          </Grid>\n          \n          <Grid item xs={12} sm={6} md={3}>\n            <Card>\n              <CardContent>\n                <Typography variant=\"h6\" color=\"secondary\">\n                  {reports.filter(r => r.type === 'EOW').length}\n                </Typography>\n                <Typography variant=\"body2\" color=\"text.secondary\">\n                  EOW Reports\n                </Typography>\n              </CardContent>\n            </Card>\n          </Grid>\n          \n          <Grid item xs={12} sm={6} md={3}>\n            <Card>\n              <CardContent>\n                <Typography variant=\"h6\" color=\"primary\">\n                  {reports.reduce((sum, r) => sum + r.message_count, 0)}\n                </Typography>\n                <Typography variant=\"body2\" color=\"text.secondary\">\n                  Total Messages\n                </Typography>\n              </CardContent>\n            </Card>\n          </Grid>\n        </Grid>\n      )}\n    </Container>\n  );\n};\n\nexport default Reports;"