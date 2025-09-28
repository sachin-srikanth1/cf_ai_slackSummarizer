import React, { useState, useRef, useEffect } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Box,
  TextField,
  Button,
  Paper,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Send, SmartToy, Person } from '@mui/icons-material';
import { apiService } from '../services/apiService';

interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      content: "Hi! I'm your Slack AI Summarizer assistant. I can help you generate EOD/EOW reports, manage your preferences, and answer questions about your Slack activity. What would you like to do?",
      sender: 'assistant',
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: inputMessage,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.sendChatMessage(inputMessage);
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: response.response || 'I received your message but couldn\'t generate a response.',
        sender: 'assistant',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send message');
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error processing your message. Please try again.',
        sender: 'assistant',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const quickActions = [
    'Generate EOD report',
    'Generate EOW report',
    'Show my preferences',
    'Sync Slack messages',
    'Help',
  ];

  const handleQuickAction = (action: string) => {
    setInputMessage(action);
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Chat with AI Assistant
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Card>
        <CardContent>
          {/* Messages Area */}
          <Box
            sx={{
              height: 500,
              overflow: 'auto',
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 1,
              p: 2,
              mb: 2,
              backgroundColor: 'grey.50',
            }}
          >
            {messages.map((message) => (
              <Box
                key={message.id}
                sx={{
                  display: 'flex',
                  mb: 2,
                  justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                }}
              >
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    maxWidth: '80%',
                    backgroundColor: message.sender === 'user' ? 'primary.main' : 'white',
                    color: message.sender === 'user' ? 'white' : 'text.primary',
                  }}
                >
                  <Box display="flex" alignItems="flex-start" mb={1}>
                    {message.sender === 'user' ? (
                      <Person sx={{ mr: 1, fontSize: 18 }} />
                    ) : (
                      <SmartToy sx={{ mr: 1, fontSize: 18 }} />
                    )}
                    <Typography variant="caption" sx={{ opacity: 0.8 }}>
                      {message.sender === 'user' ? 'You' : 'Assistant'}
                    </Typography>
                  </Box>
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                    {message.content}
                  </Typography>
                  <Typography variant="caption" sx={{ opacity: 0.6, display: 'block', mt: 1 }}>
                    {message.timestamp.toLocaleTimeString()}
                  </Typography>
                </Paper>
              </Box>
            ))}
            
            {loading && (
              <Box display="flex" justifyContent="flex-start" mb={2}>
                <Paper elevation={1} sx={{ p: 2, backgroundColor: 'white' }}>
                  <Box display="flex" alignItems="center">
                    <SmartToy sx={{ mr: 1, fontSize: 18 }} />
                    <CircularProgress size={16} sx={{ mr: 1 }} />
                    <Typography variant="body2">Assistant is typing...</Typography>
                  </Box>
                </Paper>
              </Box>
            )}
            
            <div ref={messagesEndRef} />
          </Box>

          {/* Quick Actions */}
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              Quick Actions:
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {quickActions.map((action) => (
                <Button
                  key={action}
                  size="small"
                  variant="outlined"
                  onClick={() => handleQuickAction(action)}
                  disabled={loading}
                >
                  {action}
                </Button>
              ))}
            </Box>
          </Box>

          {/* Message Input */}
          <Box display="flex" gap={1}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
            <Button
              variant="contained"
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || loading}
              sx={{ minWidth: 'auto', px: 3 }}
            >
              {loading ? <CircularProgress size={20} /> : <Send />}
            </Button>
          </Box>

          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Try asking: "Generate an EOD report", "What are my current settings?", or "Help me understand my Slack activity"
          </Typography>
        </CardContent>
      </Card>
    </Container>
  );
};

export default Chat;