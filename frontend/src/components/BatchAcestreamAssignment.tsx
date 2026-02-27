import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  Typography,
  TextField,
  Alert,
  CircularProgress
} from '@mui/material';
import { useBatchAssignAcestreams } from '../hooks/useTVChannels';

interface BatchAcestreamAssignmentProps {
  open: boolean;
  onClose: () => void;
  tvChannelId: number;
  tvChannelName: string;
}

/**
 * Component for batch assigning multiple acestream IDs to a TV channel
 */
const BatchAcestreamAssignment: React.FC<BatchAcestreamAssignmentProps> = ({ 
  open, 
  onClose, 
  tvChannelId,
  tvChannelName
}) => {
  const [aceStreamIds, setAceStreamIds] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const batchAssignMutation = useBatchAssignAcestreams();
  
  const handleSubmit = async () => {
    if (!aceStreamIds.trim()) return;
    
    // Split by commas, newlines, or spaces and filter out empty strings
    const ids = aceStreamIds
      .split(/[\s,]+/)
      .map(id => id.trim())
      .filter(id => id.length > 0);
    
    if (ids.length === 0) {
      setError('No valid acestream IDs provided');
      return;
    }
    
    try {
      setError(null);
      const result = await batchAssignMutation.mutateAsync({
        [tvChannelId]: ids
      });
      
      setSuccess(`Successfully associated ${result.success_count} acestreams. Failed to associate ${result.failure_count} acestreams.`);
      setAceStreamIds('');
      
      // Auto-close dialog after successful operation
      if (result.success_count > 0 && result.failure_count === 0) {
        setTimeout(() => {
          onClose();
          setSuccess(null);
        }, 2000);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to associate acestreams');
    }
  };
  
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Batch Associate Acestreams to {tvChannelName}
      </DialogTitle>
      <DialogContent>
        <Box my={2}>
          <Typography variant="body1" gutterBottom>
            Enter multiple acestream IDs, separated by commas, spaces, or line breaks.
          </Typography>
          
          {error && (
            <Alert severity="error" sx={{ my: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          
          {success && (
            <Alert severity="success" sx={{ my: 2 }} onClose={() => setSuccess(null)}>
              {success}
            </Alert>
          )}
          
          <TextField
            label="Acestream IDs"
            multiline
            rows={6}
            value={aceStreamIds}
            onChange={(e) => setAceStreamIds(e.target.value)}
            fullWidth
            placeholder="Enter acestream IDs here, e.g.:\nabc123def456\nxyz789\n..."
            variant="outlined"
            sx={{ mt: 2 }}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="inherit">
          Cancel
        </Button>
        <Button 
          onClick={handleSubmit} 
          color="primary" 
          variant="contained"
          disabled={!aceStreamIds.trim() || batchAssignMutation.isLoading}
        >
          {batchAssignMutation.isLoading ? (
            <CircularProgress size={24} color="inherit" />
          ) : (
            'Associate'
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default BatchAcestreamAssignment;
