import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { emailApi } from '../api/client';
import {
    Box,
    Container,
    Typography,
    Paper,
    Avatar,
    Button,
    TextField,
    Skeleton,
    Stack,
    LinearProgress,
    Alert,
} from '@mui/material';
import {
    ArrowBack as ArrowBackIcon,
    Send as SendIcon,
    AutoAwesome as AutoAwesomeIcon,
    AttachMoney as AttachMoneyIcon,
} from '@mui/icons-material';

export const EmailDetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [responseContent, setResponseContent] = useState('');
    const [pricingData, setPricingData] = useState<any>(null);
    const [roiData, setRoiData] = useState<any>(null);
    const [authenticityData, setAuthenticityData] = useState<any>(null);

    const { data: email, isLoading: isLoadingEmail, error: emailError } = useQuery({
        queryKey: ['email', id],
        queryFn: () => emailApi.getThread(id!),
        enabled: !!id,
        refetchOnWindowFocus: false,
    });

    const generateMutation = useMutation({
        mutationFn: () => emailApi.generateResponse(id!),
        onSuccess: (data) => {
            setResponseContent(data.response_draft);
            if (data.pricing_breakdown) {
                setPricingData(data.pricing_breakdown);
            }
            if (data.roi_forecast) {
                setRoiData(data.roi_forecast);
            }
            if (data.authenticity_data) {
                setAuthenticityData(data.authenticity_data);
            }
        },
    });

    const sendMutation = useMutation({
        mutationFn: () => emailApi.sendReply(id!, responseContent),
        onSuccess: () => {
            alert('Reply sent successfully!');
        },
    });

    if (isLoadingEmail) {
        return (
            <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Stack spacing={2} alignItems="center">
                    <Skeleton variant="circular" width={64} height={64} />
                    <Skeleton variant="text" width={200} />
                    <Skeleton variant="text" width={150} />
                </Stack>
            </Box>
        );
    }

    if (emailError) {
        return (
            <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Alert severity="error" sx={{ maxWidth: 400 }}>
                    Error: {(emailError as Error).message}
                </Alert>
            </Box>
        );
    }

    if (!email) return null;

    return (
        <Box sx={{ minHeight: '100vh', display: 'flex', bgcolor: 'background.default' }}>
            {/* Left Panel: Email Thread */}
            <Box sx={{ flex: 1, overflow: 'auto', maxHeight: '100vh' }}>
                {/* Back Header */}
                <Box sx={{ position: 'sticky', top: 0, bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider', px: 4, py: 2, zIndex: 10 }}>
                    <Button
                        component={Link}
                        to="/"
                        startIcon={<ArrowBackIcon />}
                        sx={{ color: 'text.secondary', '&:hover': { color: 'text.primary', bgcolor: 'transparent' } }}
                    >
                        Back to Inbox
                    </Button>
                </Box>

                <Container maxWidth="md" sx={{ py: 5 }}>
                    {/* Thread Header */}
                    <Box sx={{ mb: 5 }}>
                        <Stack direction="row" spacing={2.5} alignItems="center" sx={{ mb: 2 }}>
                            <Avatar
                                sx={{
                                    width: 64,
                                    height: 64,
                                    bgcolor: 'grey.100',
                                    color: 'text.primary',
                                    fontSize: '1.5rem',
                                    fontWeight: 700,
                                }}
                            >
                                {email.influencer_name?.charAt(0) || email.sender?.charAt(0) || 'U'}
                            </Avatar>
                            <Box>
                                <Typography variant="h2">{email.influencer_name || email.sender}</Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                                    {email.category?.replace('_', ' ')} • {new Date(email.date || email.latest_message_time || Date.now()).toLocaleDateString()}
                                </Typography>
                            </Box>
                        </Stack>
                        <Typography variant="h3" color="text.secondary" sx={{ fontWeight: 500 }}>
                            {email.subject}
                        </Typography>
                    </Box>

                    {/* Messages */}
                    <Stack spacing={3}>
                        {email.messages?.map((msg: any, idx: number) => (
                            <Paper key={msg.id || idx} sx={{ p: 4 }}>
                                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                                    <Typography variant="body1" fontWeight={600}>
                                        {msg.sender || msg.from}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        {new Date(msg.date || msg.timestamp).toLocaleString()}
                                    </Typography>
                                </Stack>
                                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', color: 'text.secondary', lineHeight: 1.7 }}>
                                    {msg.content || msg.body}
                                </Typography>
                            </Paper>
                        ))}
                    </Stack>
                </Container>
            </Box>

            {/* Right Panel: AI Assistant */}
            <Box
                sx={{
                    width: 460,
                    bgcolor: 'background.paper',
                    borderLeft: 1,
                    borderColor: 'divider',
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100vh',
                    boxShadow: '-4px 0 20px rgba(0,0,0,0.03)',
                }}
            >
                {/* AI Header */}
                <Box sx={{ px: 4, py: 3.5, borderBottom: 1, borderColor: 'divider' }}>
                    <Stack direction="row" spacing={2} alignItems="center">
                        <Box
                            sx={{
                                width: 44,
                                height: 44,
                                borderRadius: 2.5,
                                bgcolor: 'primary.main',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                boxShadow: 2,
                            }}
                        >
                            <AutoAwesomeIcon sx={{ color: 'white', fontSize: 22 }} />
                        </Box>
                        <Box>
                            <Typography variant="h4">AI Assistant</Typography>
                            <Typography variant="caption" color="text.secondary">GPT-4o + MCP</Typography>
                        </Box>
                    </Stack>
                </Box>

                {/* Loading indicator */}
                {generateMutation.isPending && <LinearProgress />}

                {/* Content */}
                <Box sx={{ flex: 1, overflow: 'auto', px: 4, py: 4 }}>
                    <Stack spacing={4}>
                        {/* Pricing Card */}
                        {pricingData && (
                            <Paper variant="outlined" sx={{ p: 3, bgcolor: 'grey.50' }}>
                                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
                                    <Typography variant="body2" fontWeight={600} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <AttachMoneyIcon fontSize="small" sx={{ color: 'success.main' }} />
                                        Fair Price Analysis
                                    </Typography>
                                    <Typography variant="h2" sx={{ fontSize: '1.75rem' }}>
                                        ${pricingData.recommended_offer.toLocaleString()}
                                    </Typography>
                                </Stack>

                                <Stack spacing={2.5}>
                                    {[
                                        { label: 'Engagement', value: pricingData.engagement_multiplier },
                                        { label: 'Niche Match', value: pricingData.niche_multiplier },
                                        { label: 'Consistency', value: pricingData.consistency_multiplier },
                                    ].map((item) => (
                                        <Box key={item.label}>
                                            <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.5 }}>
                                                <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: 0.5 }}>
                                                    {item.label}
                                                </Typography>
                                                <Typography variant="caption" fontWeight={700}>{item.value}x</Typography>
                                            </Stack>
                                            <LinearProgress
                                                variant="determinate"
                                                value={Math.min(100, (item.value / 1.5) * 100)}
                                                sx={{
                                                    height: 6,
                                                    borderRadius: 1,
                                                    bgcolor: 'grey.200',
                                                    '& .MuiLinearProgress-bar': { bgcolor: 'primary.main', borderRadius: 1 },
                                                }}
                                            />
                                        </Box>
                                    ))}
                                </Stack>
                            </Paper>
                        )}

                        {/* Compact Detailed Analytics Row */}
                        {(roiData || authenticityData) && (
                            <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
                                {/* ROI Forecast - Compact Detail */}
                                {roiData && (
                                    <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50', flex: 1 }}>
                                        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5 }}>
                                            <Typography variant="body2" fontWeight={600} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                📈 ROI Forecast
                                            </Typography>
                                            <Typography variant="body1" fontWeight={700} sx={{
                                                color: roiData.roas >= 2 ? 'success.main' : roiData.roas >= 1 ? 'warning.main' : 'error.main'
                                            }}>
                                                {roiData.roas}x ROAS
                                            </Typography>
                                        </Stack>

                                        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mb: 1.5 }}>
                                            <Box>
                                                <Typography variant="caption" color="text.secondary" display="block" sx={{ fontSize: '0.7rem' }}>Est. Revenue</Typography>
                                                <Typography variant="caption" fontWeight={700}>${roiData.estimated_revenue?.toLocaleString()}</Typography>
                                            </Box>
                                            <Box>
                                                <Typography variant="caption" color="text.secondary" display="block" sx={{ fontSize: '0.7rem' }}>Conv.</Typography>
                                                <Typography variant="caption" fontWeight={700}>{roiData.estimated_conversions}</Typography>
                                            </Box>
                                            <Box>
                                                <Typography variant="caption" color="text.secondary" display="block" sx={{ fontSize: '0.7rem' }}>Confidence</Typography>
                                                <Typography variant="caption" fontWeight={700}>{Math.round(roiData.confidence_score * 100)}%</Typography>
                                            </Box>
                                            <Box>
                                                <Typography variant="caption" color="text.secondary" display="block" sx={{ fontSize: '0.7rem' }}>Status</Typography>
                                                <Typography variant="caption" fontWeight={700} sx={{
                                                    color: roiData.roas >= 2 ? 'success.dark' : roiData.roas >= 1 ? 'warning.dark' : 'error.dark'
                                                }}>
                                                    {roiData.assessment.split(' ')[0]}
                                                </Typography>
                                            </Box>
                                        </Box>
                                    </Paper>
                                )}

                                {/* Authenticity - Compact Detail */}
                                {authenticityData && (
                                    <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50', flex: 1 }}>
                                        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5 }}>
                                            <Typography variant="body2" fontWeight={600} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                🛡️ Auth Check
                                            </Typography>
                                            <Typography variant="body1" fontWeight={700} sx={{
                                                color: authenticityData.score >= 85 ? 'success.main' : authenticityData.score >= 70 ? 'warning.main' : 'error.main'
                                            }}>
                                                {authenticityData.score}/100
                                            </Typography>
                                        </Stack>

                                        <LinearProgress
                                            variant="determinate"
                                            value={authenticityData.score}
                                            sx={{
                                                height: 4,
                                                borderRadius: 1,
                                                mb: 2,
                                                bgcolor: 'grey.200',
                                                '& .MuiLinearProgress-bar': {
                                                    bgcolor: authenticityData.score >= 85 ? 'success.main' : authenticityData.score >= 70 ? 'warning.main' : 'error.main',
                                                    borderRadius: 1
                                                },
                                            }}
                                        />

                                        <Box>
                                            <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', fontSize: '0.65rem', mb: 0.5, display: 'block' }}>
                                                Red Flags ({authenticityData.red_flags?.length || 0})
                                            </Typography>
                                            {authenticityData.red_flags?.length > 0 ? (
                                                <Stack spacing={0.5}>
                                                    {authenticityData.red_flags.slice(0, 2).map((flag: any, idx: number) => (
                                                        <Typography key={idx} variant="caption" sx={{
                                                            display: 'block',
                                                            whiteSpace: 'nowrap',
                                                            overflow: 'hidden',
                                                            textOverflow: 'ellipsis',
                                                            color: flag.severity === 'high' ? 'error.main' : 'text.secondary',
                                                            fontSize: '0.7rem'
                                                        }}>
                                                            • {flag.flag}
                                                        </Typography>
                                                    ))}
                                                    {authenticityData.red_flags.length > 2 && (
                                                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                                                            + {authenticityData.red_flags.length - 2} more
                                                        </Typography>
                                                    )}
                                                </Stack>
                                            ) : (
                                                <Typography variant="caption" color="success.main" sx={{ fontSize: '0.7rem' }}>
                                                    No anomalies detected
                                                </Typography>
                                            )}
                                        </Box>
                                    </Paper>
                                )}
                            </Stack>
                        )}

                        {/* Response Area */}
                        <Box>
                            <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: 1, mb: 1.5, display: 'block' }}>
                                Draft Response
                            </Typography>

                            {generateMutation.isPending ? (
                                <Paper variant="outlined" sx={{ p: 3, bgcolor: 'grey.50' }}>
                                    <Stack spacing={1.5}>
                                        <Skeleton variant="text" width="75%" />
                                        <Skeleton variant="text" width="100%" />
                                        <Skeleton variant="text" width="85%" />
                                    </Stack>
                                </Paper>
                            ) : (
                                <TextField
                                    multiline
                                    rows={14}
                                    fullWidth
                                    placeholder="Click generate to create a draft..."
                                    value={responseContent}
                                    onChange={(e) => setResponseContent(e.target.value)}
                                    sx={{
                                        '& .MuiOutlinedInput-root': {
                                            bgcolor: 'grey.50',
                                        },
                                    }}
                                />
                            )}
                        </Box>
                    </Stack>
                </Box>

                {/* Footer Actions */}
                <Box sx={{ px: 4, py: 3, borderTop: 1, borderColor: 'divider' }}>
                    <Stack spacing={2}>
                        <Button
                            variant="contained"
                            size="large"
                            fullWidth
                            onClick={() => generateMutation.mutate()}
                            disabled={generateMutation.isPending || sendMutation.isPending}
                            startIcon={generateMutation.isPending ? null : <AutoAwesomeIcon />}
                            sx={{ py: 1.5 }}
                        >
                            {generateMutation.isPending ? 'Analyzing...' : 'Generate Response'}
                        </Button>

                        {responseContent && (
                            <Button
                                variant="outlined"
                                size="large"
                                fullWidth
                                onClick={() => sendMutation.mutate()}
                                disabled={sendMutation.isPending}
                                startIcon={<SendIcon />}
                                sx={{ py: 1.5, color: 'text.secondary', borderColor: 'divider' }}
                            >
                                Approve & Send
                            </Button>
                        )}
                    </Stack>
                </Box>
            </Box>
        </Box>
    );
};
