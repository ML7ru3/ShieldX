import { useEffect, useRef, useState, useCallback } from 'react'
import {
  Box, Heading, Text, Table, Thead, Tbody, Tr, Th, Td,
  Badge, Spinner, Flex, VStack, HStack, SimpleGrid, Button, IconButton, useToast,
  useColorModeValue,
} from '@chakra-ui/react'
import { ArrowBackIcon, AddIcon, DownloadIcon } from '@chakra-ui/icons'
import type { Agent, RecentDomain } from '../types'
import { whitelistApi, recentDomainsApi } from '../api'

interface Props {
  agent: Agent
  onBack: () => void
}

export default function AgentDetail({ agent, onBack }: Props) {
  const [domains, setDomains] = useState<RecentDomain[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<string>('')
  const [addingDomain, setAddingDomain] = useState<Record<number, boolean>>({})
  const toast = useToast()
  const bg = useColorModeValue('white', 'gray.800')
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const formatTime = (t: string) => new Date(t).toLocaleString()
  const timeAgo = (t: string) => {
    const diff = Date.now() - new Date(t).getTime()
    const sec = Math.floor(diff / 1000)
    if (sec < 60) return `${sec}s ago`
    const min = Math.floor(sec / 60)
    if (min < 60) return `${min}m ago`
    return `${Math.floor(min / 60)}h ago`
  }

  const fetchDomains = useCallback(() => {
    recentDomainsApi.getByAgent(agent.agent_id)
      .then(res => {
        setDomains(res.data)
        setLastUpdated(new Date().toLocaleTimeString())
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [agent.agent_id])

  useEffect(() => {
    fetchDomains()
    intervalRef.current = setInterval(fetchDomains, 30000)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [fetchDomains])

  const handleAddToWhitelist = async (domain: string, id: number) => {
    setAddingDomain(prev => ({ ...prev, [id]: true }))
    try {
      await whitelistApi.create({ domain })
      toast({ title: `"${domain}" added to whitelist`, status: 'success', duration: 2000 })
    } catch (err: any) {
      toast({ title: err.response?.data?.detail || 'Failed to add domain', status: 'error', duration: 3000 })
    }
    setAddingDomain(prev => ({ ...prev, [id]: false }))
  }

  const handleDownloadLog = () => {
    recentDomainsApi.downloadLog(agent.agent_id)
      .then(res => {
        const blob = new Blob([res.data], { type: 'text/plain' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url; a.download = `recent_domains_${agent.agent_id}.log`
        a.click()
        URL.revokeObjectURL(url)
      })
      .catch(() => toast({ title: 'Failed to download log', status: 'error', duration: 3000 }))
  }

  if (loading) return <Flex h="60vh" align="center" justify="center"><Spinner size="xl" /></Flex>

  return (
    <Box p={6}>
      <HStack spacing={4} mb={8}>
        <IconButton aria-label="Back" icon={<ArrowBackIcon />} borderRadius="full" onClick={onBack} />
        <VStack align="start" spacing={0}>
          <Heading size="lg" fontWeight="bold" color="gray.800">{agent.hostname}</Heading>
          <Text color="gray.500" fontSize="sm">Agent Details</Text>
        </VStack>
      </HStack>

      {/* Agent Info */}
      <SimpleGrid columns={{ base: 1, md: 4 }} spacing={4} mb={8}>
        <Box bg={bg} borderRadius="2xl" boxShadow="lg" p={5} border="1px" borderColor="gray.100">
          <Text fontSize="xs" color="gray.400" fontWeight="medium" textTransform="uppercase" mb={1}>Agent ID</Text>
          <Text fontWeight="semibold" fontFamily="mono" fontSize="sm">{agent.agent_id}</Text>
        </Box>
        <Box bg={bg} borderRadius="2xl" boxShadow="lg" p={5} border="1px" borderColor="gray.100">
          <Text fontSize="xs" color="gray.400" fontWeight="medium" textTransform="uppercase" mb={1}>IP Address</Text>
          <Text fontWeight="semibold" fontFamily="mono">{agent.ip}</Text>
        </Box>
        <Box bg={bg} borderRadius="2xl" boxShadow="lg" p={5} border="1px" borderColor="gray.100">
          <Text fontSize="xs" color="gray.400" fontWeight="medium" textTransform="uppercase" mb={1}>Status</Text>
          <Badge colorScheme={agent.status === 'active' ? 'green' : 'red'} px={3} py={1} borderRadius="full">
            {agent.status}
          </Badge>
        </Box>
        <Box bg={bg} borderRadius="2xl" boxShadow="lg" p={5} border="1px" borderColor="gray.100">
          <Text fontSize="xs" color="gray.400" fontWeight="medium" textTransform="uppercase" mb={1}>Last Seen</Text>
          <Text fontWeight="semibold" fontSize="sm">{formatTime(agent.last_seen)}</Text>
        </Box>
      </SimpleGrid>

      {/* Recent Domains */}
      <Box bg={bg} borderRadius="2xl" boxShadow="lg" overflow="hidden" border="1px" borderColor="gray.100">
        <Flex justify="space-between" align="center" px={6} py={4} borderBottom="1px" borderColor="gray.100">
          <VStack align="start" spacing={0}>
            <Heading size="sm" fontWeight="bold">Recent Domains</Heading>
            <Text fontSize="xs" color="gray.400">
              {domains.length} domains tracked
              {lastUpdated && ` · Last updated: ${timeAgo(lastUpdated)}`}
            </Text>
          </VStack>
          <Button
            leftIcon={<DownloadIcon />}
            size="sm"
            variant="outline"
            borderRadius="full"
            onClick={handleDownloadLog}
          >
            Download .log
          </Button>
        </Flex>
        <Table variant="simple">
          <Thead bg="gray.50">
            <Tr>
              <Th>Domain</Th>
              <Th>IP</Th>
              <Th>Last Seen</Th>
              <Th textAlign="center">Action</Th>
            </Tr>
          </Thead>
          <Tbody>
            {domains.map(d => (
              <Tr key={d.id} _hover={{ bg: 'gray.50' }} transition="background 0.2s">
                <Td fontWeight="medium">
                  <Badge colorScheme="purple" px={3} py={1} borderRadius="full" fontSize="sm">
                    {d.domain}
                  </Badge>
                </Td>
                <Td fontFamily="mono" fontSize="sm" color="gray.600">{d.ip}</Td>
                <Td fontSize="sm" color="gray.500">{timeAgo(d.last_seen)}</Td>
                <Td>
                  <Flex justify="center">
                    <Button
                      size="sm"
                      leftIcon={<AddIcon />}
                      colorScheme="green"
                      variant="ghost"
                      borderRadius="full"
                      isLoading={addingDomain[d.id]}
                      onClick={() => handleAddToWhitelist(d.domain, d.id)}
                    >
                      Add to Whitelist
                    </Button>
                  </Flex>
                </Td>
              </Tr>
            ))}
            {domains.length === 0 && (
              <Tr><Td colSpan={4} textAlign="center" py={8} color="gray.400">No recent domains reported</Td></Tr>
            )}
          </Tbody>
        </Table>
      </Box>
    </Box>
  )
}
