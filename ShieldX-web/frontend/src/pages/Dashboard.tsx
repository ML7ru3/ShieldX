import { useEffect, useState } from 'react'
import {
  Box, SimpleGrid, Stat, StatLabel, StatNumber, StatHelpText,
  Heading, Text, VStack, Icon, Flex, Spinner, Alert, AlertIcon,
} from '@chakra-ui/react'
import { FiServer, FiAlertTriangle, FiShield } from 'react-icons/fi'

import api from '../api'
import type { Agent, MalwareAlert, WhitelistDomain } from '../types'

function StatCard({ icon, label, value, helpText, color }: {
  icon: React.ElementType; label: string; value: string | number;
  helpText?: string; color: string
}) {
  return (
    <Stat px={6} py={5} bg="white" borderRadius="2xl" boxShadow="lg"
      border="1px" borderColor="gray.100" _hover={{ transform: 'translateY(-2px)', boxShadow: 'xl' }}
      transition="all 0.2s">
      <Flex align="center" gap={4}>
        <Flex w={14} h={14} borderRadius="xl" bg={`${color}.50`} align="center" justify="center">
          <Icon as={icon} w={7} h={7} color={`${color}.500`} />
        </Flex>
        <Box>
          <StatLabel fontSize="sm" color="gray.500" fontWeight="medium">{label}</StatLabel>
          <StatNumber fontSize="2xl" fontWeight="bold">{value}</StatNumber>
          {helpText && <StatHelpText fontSize="xs" color="gray.400">{helpText}</StatHelpText>}
        </Box>
      </Flex>
    </Stat>
  )
}

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [alerts, setAlerts] = useState<MalwareAlert[]>([])
  const [domains, setDomains] = useState<WhitelistDomain[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api.get<Agent[]>('/heartbeat/').catch(() => ({ data: [] as Agent[] })),
      api.get<MalwareAlert[]>('/report-malware/').catch(() => ({ data: [] as MalwareAlert[] })),
      api.get<{ domains: WhitelistDomain[] }>('/domain/whitelist/').catch(() => ({ data: { domains: [] } })),
    ])
      .then(([agentsRes, alertsRes, domainsRes]) => {
        setAgents(agentsRes.data)
        setAlerts(alertsRes.data)
        setDomains(domainsRes.data.domains)
        setLoading(false)
      })
      .catch(() => { setError('Could not connect to backend'); setLoading(false) })
  }, [])

  if (loading) return <Flex h="60vh" align="center" justify="center"><Spinner size="xl" /></Flex>

  return (
    <Box p={6}>
      <VStack align="start" spacing={1} mb={8}>
        <Heading size="lg" fontWeight="bold" color="gray.800">Dashboard</Heading>
        <Text color="gray.500" fontSize="sm">ShieldX Agent Monitoring Overview</Text>
      </VStack>

      {error && <Alert status="warning" mb={6} borderRadius="xl"><AlertIcon />{error}</Alert>}

      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6}>
        <StatCard icon={FiServer} label="Registered Agents" value={agents.length} color="blue"
          helpText={agents.length > 0 ? `Last active: ${agents[0]?.hostname || 'N/A'}` : undefined} />
        <StatCard icon={FiAlertTriangle} label="Malware Alerts" value={alerts.length} color="red"
          helpText="Total reported incidents" />
        <StatCard icon={FiShield} label="Whitelisted Domains" value={domains.length} color="green"
          helpText="Trusted domains" />
      </SimpleGrid>
    </Box>
  )
}
