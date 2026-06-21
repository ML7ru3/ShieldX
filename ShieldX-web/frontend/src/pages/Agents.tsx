import { useEffect, useState } from 'react'
import {
  Box, Heading, Text, Table, Thead, Tbody, Tr, Th, Td,
  Badge, Spinner, Flex, VStack, Alert, AlertIcon,
  useColorModeValue,
} from '@chakra-ui/react'
import axios from 'axios'
import type { Agent } from '../types'

export default function Agents() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const bg = useColorModeValue('white', 'gray.800')

  useEffect(() => {
    axios.get('http://localhost:8000/heartbeat/')
      .then(res => {
        const data = Array.isArray(res.data) ? res.data : [res.data]
        setAgents(data)
        setLoading(false)
      })
      .catch(() => { setError('Failed to fetch agents'); setLoading(false) })
  }, [])

  if (loading) return <Flex h="60vh" align="center" justify="center"><Spinner size="xl" /></Flex>

  const formatTime = (t: string) => new Date(t).toLocaleString()

  return (
    <Box p={6}>
      <VStack align="start" spacing={1} mb={8}>
        <Heading size="lg" fontWeight="bold" color="gray.800">Agents</Heading>
        <Text color="gray.500" fontSize="sm">All registered ShieldX agents</Text>
      </VStack>

      {error && <Alert status="warning" mb={6} borderRadius="xl"><AlertIcon />{error}</Alert>}

      <Box bg={bg} borderRadius="2xl" boxShadow="lg" overflow="hidden" border="1px" borderColor="gray.100">
        <Table variant="simple">
          <Thead bg="gray.50">
            <Tr>
              <Th>Agent ID</Th>
              <Th>Hostname</Th>
              <Th>IP Address</Th>
              <Th>Status</Th>
              <Th>First Seen</Th>
              <Th>Last Seen</Th>
            </Tr>
          </Thead>
          <Tbody>
            {agents.map(agent => (
              <Tr key={agent.agent_id} _hover={{ bg: 'gray.50' }} transition="background 0.2s">
                <Td fontWeight="medium" fontFamily="mono" fontSize="sm">{agent.agent_id}</Td>
                <Td>{agent.hostname}</Td>
                <Td fontFamily="mono" fontSize="sm">{agent.ip}</Td>
                <Td>
                  <Badge colorScheme={agent.status === 'active' ? 'green' : 'red'} px={3} py={1} borderRadius="full">
                    {agent.status}
                  </Badge>
                </Td>
                <Td fontSize="sm" color="gray.500">{formatTime(agent.first_seen)}</Td>
                <Td fontSize="sm" color="gray.500">{formatTime(agent.last_seen)}</Td>
              </Tr>
            ))}
            {agents.length === 0 && (
              <Tr><Td colSpan={6} textAlign="center" py={8} color="gray.400">No agents registered yet</Td></Tr>
            )}
          </Tbody>
        </Table>
      </Box>
    </Box>
  )
}
