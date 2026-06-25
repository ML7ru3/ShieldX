import { useEffect, useState } from 'react'
import {
  Box, Heading, Text, Table, Thead, Tbody, Tr, Th, Td,
  Badge, Spinner, Flex, VStack, Alert, AlertIcon,
  Button, Input, Modal, ModalOverlay, ModalContent, ModalHeader,
  ModalBody, ModalFooter, ModalCloseButton, useDisclosure, useToast,
  IconButton, HStack, useColorModeValue, Textarea, Switch, FormControl, FormLabel,
} from '@chakra-ui/react'
import { AddIcon, DeleteIcon, EditIcon } from '@chakra-ui/icons'
import axios from 'axios'
import type { WhitelistDomain } from '../types'
import { whitelistApi } from '../api'

const API = 'http://localhost:8000/domain/whitelist'

export default function Whitelist() {
  const [domains, setDomains] = useState<WhitelistDomain[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editDomain, setEditDomain] = useState<WhitelistDomain | null>(null)
  const [formDomain, setFormDomain] = useState('')
  const [formNotes, setFormNotes] = useState('')
  const [whitelistEnabled, setWhitelistEnabled] = useState(true)
  const [toggling, setToggling] = useState(false)
  const toast = useToast()
  const bg = useColorModeValue('white', 'gray.800')

  const { isOpen, onOpen, onClose } = useDisclosure()

  const fetchDomains = () => {
    whitelistApi.getAll()
      .then(res => {
        setDomains(res.data.domains || [])
        setWhitelistEnabled(res.data.whitelist_enabled)
        setLoading(false)
      })
      .catch(() => { setError('Failed to fetch whitelist'); setLoading(false) })
  }

  useEffect(() => { fetchDomains() }, [])

  const handleToggle = async (enabled: boolean) => {
    setToggling(true)
    try {
      await whitelistApi.setToggle(enabled)
      setWhitelistEnabled(enabled)
      toast({ title: `Whitelist ${enabled ? 'enabled' : 'disabled'}`, status: 'success', duration: 2000 })
    } catch {
      toast({ title: 'Failed to update whitelist toggle', status: 'error', duration: 3000 })
    }
    setToggling(false)
  }

  const openAdd = () => {
    setEditDomain(null); setFormDomain(''); setFormNotes(''); onOpen()
  }

  const openEdit = (d: WhitelistDomain) => {
    setEditDomain(d); setFormDomain(d.domain); setFormNotes(d.notes || ''); onOpen()
  }

  const handleSave = async () => {
    if (!formDomain.trim()) {
      toast({ title: 'Domain is required', status: 'warning', duration: 2000 })
      return
    }
    try {
      if (editDomain) {
        await axios.put(`${API}/${editDomain.id}`, { domain: formDomain.trim(), notes: formNotes.trim() || null })
        toast({ title: 'Domain updated', status: 'success', duration: 2000 })
      } else {
        await axios.post(`${API}/`, { domain: formDomain.trim(), notes: formNotes.trim() || null })
        toast({ title: 'Domain added', status: 'success', duration: 2000 })
      }
      onClose(); fetchDomains()
    } catch (err: any) {
      toast({ title: err.response?.data?.detail || 'Error saving domain', status: 'error', duration: 3000 })
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Remove this domain from whitelist?')) return
    try {
      await axios.delete(`${API}/${id}`)
      toast({ title: 'Domain removed', status: 'success', duration: 2000 })
      fetchDomains()
    } catch {
      toast({ title: 'Error deleting domain', status: 'error', duration: 3000 })
    }
  }

  if (loading) return <Flex h="60vh" align="center" justify="center"><Spinner size="xl" /></Flex>

  return (
    <Box p={6}>
      <Flex justify="space-between" align="center" mb={8}>
        <VStack align="start" spacing={1}>
          <Heading size="lg" fontWeight="bold" color="gray.800">Whitelist Domains</Heading>
          <Text color="gray.500" fontSize="sm">Manage trusted domains</Text>
        </VStack>
        <HStack spacing={4}>
          <FormControl display="flex" alignItems="center">
            <FormLabel htmlFor="whitelist-toggle" mb="0" fontSize="sm" fontWeight="medium" color="gray.600">
              Enable Whitelist
            </FormLabel>
            <Switch
              id="whitelist-toggle"
              colorScheme="green"
              isChecked={whitelistEnabled}
              isDisabled={toggling}
              onChange={e => handleToggle(e.target.checked)}
              size="lg"
            />
          </FormControl>
          <Button leftIcon={<AddIcon />} colorScheme="blue" borderRadius="full" px={6} onClick={openAdd}
            _hover={{ transform: 'translateY(-1px)', boxShadow: 'lg' }} transition="all 0.2s">
            Add Domain
          </Button>
        </HStack>
      </Flex>

      {!whitelistEnabled && (
        <Alert status="warning" mb={6} borderRadius="xl">
          <AlertIcon />
          Domain whitelist is currently disabled. All domains will be allowed.
        </Alert>
      )}

      {error && <Alert status="warning" mb={6} borderRadius="xl"><AlertIcon />{error}</Alert>}

      <Box bg={bg} borderRadius="2xl" boxShadow="lg" overflow="hidden" border="1px" borderColor="gray.100">
        <Table variant="simple">
          <Thead bg="gray.50">
            <Tr>
              <Th>Domain</Th>
              <Th>Notes</Th>
              <Th>Date Added</Th>
              <Th textAlign="center">Actions</Th>
            </Tr>
          </Thead>
          <Tbody>
            {domains.map(d => (
              <Tr key={d.id} _hover={{ bg: 'gray.50' }} transition="background 0.2s">
                <Td fontWeight="medium">
                  <Badge colorScheme="green" px={3} py={1} borderRadius="full" fontSize="sm">
                    {d.domain}
                  </Badge>
                </Td>
                <Td fontSize="sm" color="gray.600">{d.notes || '—'}</Td>
                <Td fontSize="sm" color="gray.500">{new Date(d.date_added).toLocaleDateString()}</Td>
                <Td>
                  <HStack justify="center" spacing={2}>
                    <IconButton aria-label="Edit" icon={<EditIcon />} size="sm" colorScheme="blue" variant="ghost"
                      borderRadius="full" onClick={() => openEdit(d)} />
                    <IconButton aria-label="Delete" icon={<DeleteIcon />} size="sm" colorScheme="red" variant="ghost"
                      borderRadius="full" onClick={() => handleDelete(d.id)} />
                  </HStack>
                </Td>
              </Tr>
            ))}
            {domains.length === 0 && (
              <Tr><Td colSpan={4} textAlign="center" py={8} color="gray.400">No whitelisted domains</Td></Tr>
            )}
          </Tbody>
        </Table>
      </Box>

      <Modal isOpen={isOpen} onClose={onClose} isCentered>
        <ModalOverlay backdropFilter="blur(4px)" />
        <ModalContent borderRadius="2xl">
          <ModalHeader>{editDomain ? 'Edit Domain' : 'Add Domain'}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <Input
                placeholder="example.com"
                value={formDomain}
                onChange={e => setFormDomain(e.target.value)}
                borderRadius="xl" size="lg"
              />
              <Textarea
                placeholder="Notes (optional)"
                value={formNotes}
                onChange={e => setFormNotes(e.target.value)}
                borderRadius="xl" rows={3}
              />
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose} borderRadius="full">Cancel</Button>
            <Button colorScheme="blue" onClick={handleSave} borderRadius="full" px={8}>
              {editDomain ? 'Update' : 'Add'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  )
}
