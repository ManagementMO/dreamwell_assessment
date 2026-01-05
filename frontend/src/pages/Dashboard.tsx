import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { emailApi } from '../api/client';
import { Link } from 'react-router-dom';
import {
    Box,
    Container,
    Typography,
    Paper,
    Avatar,
    Chip,
    IconButton,
    Skeleton,
    Stack,
    Divider,
} from '@mui/material';
import {
    Mail as MailIcon,
    ChevronRight as ChevronRightIcon,
    Refresh as RefreshIcon,
    Inbox as InboxIcon,
} from '@mui/icons-material';

export const Dashboard: React.FC = () => {
    const { data: emails, isLoading, error, refetch, isFetching } = useQuery({
        queryKey: ['emails'],
        queryFn: () => emailApi.listEmails(20),
        refetchOnWindowFocus: false,
    });

    if (isLoading) {
        return (
            <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Stack alignItems="center" spacing={3}>
                    <Skeleton variant="rounded" width={64} height={64} sx={{ borderRadius: 3 }} />
                    <Skeleton variant="text" width={150} />
                </Stack>
            </Box>
        );
    }

    if (error) {
        return (
            <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Paper sx={{ p: 6, textAlign: 'center', maxWidth: 400 }}>
                    <Typography color="error" gutterBottom>Error: {(error as Error).message}</Typography>
                    <Box component="button" onClick={() => refetch()} sx={{ mt: 2, px: 4, py: 1.5, bgcolor: 'primary.main', color: 'white', border: 'none', borderRadius: 2, cursor: 'pointer', fontWeight: 600 }}>
                        Retry
                    </Box>
                </Paper>
            </Box>
        );
    }

    const getStatusColor = (status: string) => {
        const colors: Record<string, { bg: string; text: string }> = {
            new: { bg: '#e0f2fe', text: '#0369a1' },
            processed: { bg: '#fef3c7', text: '#b45309' },
            replied: { bg: '#dcfce7', text: '#047857' },
        };
        return colors[status] || colors.new;
    };

    return (
        <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
            {/* Header */}
            <Box sx={{ bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}>
                <Container maxWidth="lg" sx={{ py: 4 }}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Stack direction="row" spacing={2.5} alignItems="center">
                            <Box
                                sx={{
                                    width: 48,
                                    height: 48,
                                    borderRadius: 3,
                                    bgcolor: 'primary.main',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    boxShadow: 2,
                                }}
                            >
                                <MailIcon sx={{ color: 'white', fontSize: 24 }} />
                            </Box>
                            <Box>
                                <Typography variant="h1" sx={{ fontSize: '1.75rem' }}>Dreamwell</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    AI-Powered Influencer Management
                                </Typography>
                            </Box>
                        </Stack>

                        <IconButton
                            onClick={() => refetch()}
                            disabled={isFetching}
                            sx={{
                                border: 1,
                                borderColor: 'divider',
                                borderRadius: 2,
                                px: 2,
                                '&:hover': { bgcolor: 'action.hover' },
                            }}
                        >
                            <RefreshIcon sx={{ fontSize: 20, animation: isFetching ? 'spin 1s linear infinite' : 'none', '@keyframes spin': { '100%': { transform: 'rotate(360deg)' } } }} />
                            <Typography variant="body2" sx={{ ml: 1, fontWeight: 500 }}>
                                {isFetching ? 'Refreshing...' : 'Refresh'}
                            </Typography>
                        </IconButton>
                    </Stack>
                </Container>
            </Box>

            <Container maxWidth="lg" sx={{ py: 5 }}>
                {/* Stats Row */}
                <Stack direction="row" spacing={3} sx={{ mb: 5 }}>
                    {[
                        { label: 'Total Threads', value: emails?.length || 0 },
                        { label: 'Pending Review', value: emails?.filter(e => e.status === 'new').length || 0 },
                        { label: 'Processed', value: emails?.filter(e => e.status === 'processed').length || 0 },
                    ].map((stat) => (
                        <Paper key={stat.label} sx={{ flex: 1, p: 4 }}>
                            <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: 1 }}>
                                {stat.label}
                            </Typography>
                            <Typography variant="h1" sx={{ mt: 1, fontSize: '2.5rem' }}>
                                {stat.value}
                            </Typography>
                        </Paper>
                    ))}
                </Stack>

                {/* Inbox Section */}
                <Paper sx={{ overflow: 'hidden' }}>
                    {/* Section Header */}
                    <Box sx={{ px: 4, py: 3, borderBottom: 1, borderColor: 'divider' }}>
                        <Stack direction="row" alignItems="center" spacing={2}>
                            <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: 'action.hover' }}>
                                <InboxIcon sx={{ fontSize: 22, color: 'text.secondary' }} />
                            </Box>
                            <Typography variant="h3">Inbox</Typography>
                            <Typography variant="body2" color="text.secondary">
                                {emails?.length || 0} conversations
                            </Typography>
                        </Stack>
                    </Box>

                    {/* Email List */}
                    <Box>
                        {emails?.map((email, index) => (
                            <React.Fragment key={email.thread_id}>
                                <Box
                                    component={Link}
                                    to={`/email/${email.thread_id}`}
                                    sx={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        px: 4,
                                        py: 3,
                                        textDecoration: 'none',
                                        color: 'inherit',
                                        transition: 'background-color 0.15s',
                                        '&:hover': {
                                            bgcolor: 'action.hover',
                                            '& .chevron': { transform: 'translateX(4px)', color: 'text.primary' },
                                        },
                                    }}
                                >
                                    <Avatar
                                        sx={{
                                            width: 48,
                                            height: 48,
                                            bgcolor: 'grey.100',
                                            color: 'text.secondary',
                                            fontSize: '1rem',
                                            mr: 2.5,
                                        }}
                                    >
                                        {email.influencer_name?.charAt(0) || 'U'}
                                    </Avatar>

                                    <Box sx={{ flex: 1, minWidth: 0 }}>
                                        <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 0.5 }}>
                                            <Typography variant="body1" fontWeight={600} noWrap>
                                                {email.influencer_name || email.sender}
                                            </Typography>
                                            <Chip
                                                label={email.status.toUpperCase()}
                                                size="small"
                                                sx={{
                                                    height: 22,
                                                    fontSize: '0.625rem',
                                                    bgcolor: getStatusColor(email.status).bg,
                                                    color: getStatusColor(email.status).text,
                                                    fontWeight: 700,
                                                }}
                                            />
                                        </Stack>
                                        <Stack direction="row" alignItems="center" spacing={1} sx={{ color: 'text.secondary' }}>
                                            <Typography variant="body2">{email.brand}</Typography>
                                            <Typography variant="body2">•</Typography>
                                            <Typography variant="body2" fontWeight={500}>
                                                {email.category?.replace('_', ' ')}
                                            </Typography>
                                        </Stack>
                                    </Box>

                                    <Stack direction="row" alignItems="center" spacing={3}>
                                        <Typography variant="body2" color="text.secondary">
                                            {email.latest_message_time ? new Date(email.latest_message_time).toLocaleDateString() : ''}
                                        </Typography>
                                        <ChevronRightIcon
                                            className="chevron"
                                            sx={{ color: 'text.disabled', fontSize: 22, transition: 'all 0.15s' }}
                                        />
                                    </Stack>
                                </Box>
                                {index < (emails?.length || 0) - 1 && <Divider />}
                            </React.Fragment>
                        ))}
                    </Box>

                    {(!emails || emails.length === 0) && (
                        <Box sx={{ py: 10, textAlign: 'center' }}>
                            <MailIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                            <Typography color="text.secondary">No emails found</Typography>
                        </Box>
                    )}
                </Paper>
            </Container>
        </Box>
    );
};
