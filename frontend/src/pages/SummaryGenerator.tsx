import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Chip,
  Box,
  Alert,
  CircularProgress,
  FormControlLabel,
  Switch,
} from '@mui/material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { Download, Send } from '@mui/icons-material';
import { apiService, SummaryRequest, SlackChannel } from '../services/apiService';

const SummaryGenerator: React.FC = () => {
  const [summaryType, setSummaryType] = useState<'EOD' | 'EOW'>('EOD');
  const [startDate, setStartDate] = useState<Date>(new Date());
  const [endDate, setEndDate] = useState<Date>(new Date());
  const [selectedChannels, setSelectedChannels] = useState<string[]>([]);
  const [customPrompt, setCustomPrompt] = useState('');
  const [useCustomPrompt, setUseCustomPrompt] = useState(false);
  const [channels, setChannels] = useState<SlackChannel[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [generatedSummary, setGeneratedSummary] = useState<string | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  useEffect(() => {
    loadChannels();
    setDefaultDateRange();
  }, [summaryType]);

  const loadChannels = async () => {
    try {
      const channelData = await apiService.getSlackChannels();
      setChannels(channelData);
    } catch (err) {
      setError('Failed to load Slack channels');
    }
  };

  const setDefaultDateRange = () => {
    const now = new Date();
    if (summaryType === 'EOD') {
      // Today from start of day to now
      const start = new Date(now);
      start.setHours(0, 0, 0, 0);
      setStartDate(start);
      setEndDate(now);
    } else {
      // This week from Monday to now
      const start = new Date(now);
      const dayOfWeek = start.getDay();
      const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
      start.setDate(start.getDate() - daysToMonday);
      start.setHours(0, 0, 0, 0);
      setStartDate(start);
      setEndDate(now);
    }
  };

  const handleChannelToggle = (channelId: string) => {
    setSelectedChannels(prev => 
      prev.includes(channelId) 
        ? prev.filter(id => id !== channelId)
        : [...prev, channelId]
    );
  };

  const handleGenerate = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const request: SummaryRequest = {
        type: summaryType,
        date_range: {
          start: startDate.toISOString(),
          end: endDate.toISOString(),
        },
        channels: selectedChannels.length > 0 ? selectedChannels : undefined,
        custom_prompt: useCustomPrompt ? customPrompt : undefined,
      };

      const response = await apiService.generateSummary(request);
      setGeneratedSummary(response.summary);
      setPdfUrl(response.pdf_url);
      setSuccess(`${summaryType} summary generated successfully! Processed ${response.message_count} messages.`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate summary');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!pdfUrl) return;
    
    try {
      const summaryId = pdfUrl.split('/').pop()?.replace('/pdf', '');
      if (summaryId) {
        const blob = await apiService.downloadReport(summaryId);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${summaryType}_summary.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      setError('Failed to download PDF');
    }
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Generate Summary Report
        </Typography>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

        <Grid container spacing={3}>
          {/* Configuration Panel */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Report Configuration
                </Typography>

                {/* Summary Type */}
                <FormControl fullWidth sx={{ mb: 3 }}>
                  <InputLabel>Report Type</InputLabel>
                  <Select
                    value={summaryType}
                    label="Report Type"
                    onChange={(e) => setSummaryType(e.target.value as 'EOD' | 'EOW')}
                  >
                    <MenuItem value="EOD">End of Day (EOD)</MenuItem>
                    <MenuItem value="EOW">End of Week (EOW)</MenuItem>
                  </Select>
                </FormControl>

                {/* Date Range */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Date Range
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <DateTimePicker
                        label="Start Date"
                        value={startDate}
                        onChange={(newValue) => newValue && setStartDate(newValue)}
                        slotProps={{ textField: { fullWidth: true, size: 'small' } }}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <DateTimePicker
                        label="End Date"
                        value={endDate}
                        onChange={(newValue) => newValue && setEndDate(newValue)}
                        slotProps={{ textField: { fullWidth: true, size: 'small' } }}
                      />
                    </Grid>
                  </Grid>
                </Box>

                {/* Channel Selection */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Channels (Optional)
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Leave empty to include all channels
                  </Typography>
                  <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                    {channels.map((channel) => (
                      <Chip
                        key={channel.id}
                        label={`#${channel.name}`}
                        clickable
                        color={selectedChannels.includes(channel.id) ? 'primary' : 'default'}
                        onClick={() => handleChannelToggle(channel.id)}
                        sx={{ m: 0.5 }}
                      />
                    ))}
                  </Box>
                </Box>

                {/* Custom Prompt */}
                <FormControlLabel
                  control={
                    <Switch
                      checked={useCustomPrompt}
                      onChange={(e) => setUseCustomPrompt(e.target.checked)}
                    />
                  }
                  label="Use Custom Prompt"
                  sx={{ mb: 2 }}
                />

                {useCustomPrompt && (
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Custom Prompt"
                    placeholder="Enter custom instructions for the AI summary..."
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    sx={{ mb: 3 }}
                  />
                )}

                {/* Generate Button */}
                <Button
                  variant="contained"
                  fullWidth
                  size="large"
                  startIcon={loading ? <CircularProgress size={20} /> : <Send />}
                  onClick={handleGenerate}
                  disabled={loading}
                >
                  {loading ? 'Generating...' : `Generate ${summaryType} Summary`}
                </Button>
              </CardContent>
            </Card>
          </Grid>

          {/* Preview Panel */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Generated Summary
                </Typography>

                {generatedSummary ? (
                  <>
                    <Box
                      sx={{
                        maxHeight: 400,
                        overflow: 'auto',
                        p: 2,
                        bgcolor: 'grey.50',
                        borderRadius: 1,
                        mb: 2,
                      }}
                    >
                      <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                        {generatedSummary}
                      </Typography>
                    </Box>
                    
                    {pdfUrl && (
                      <Button
                        variant="outlined"
                        startIcon={<Download />}
                        onClick={handleDownload}
                        fullWidth
                      >
                        Download PDF Report
                      </Button>
                    )}
                  </>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Configure your settings and click "Generate" to create a summary.
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </LocalizationProvider>
  );
};

export default SummaryGenerator;