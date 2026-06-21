import { useState } from 'react'
import {
  Box, Flex, Text, Icon, VStack, HStack, Divider, useColorMode,
  IconButton, Avatar, AvatarBadge,
} from '@chakra-ui/react'
import {
  FiServer, FiAlertTriangle, FiShield, FiGrid, FiMoon, FiSun,
} from 'react-icons/fi'
import Dashboard from './pages/Dashboard'
import Agents from './pages/Agents'
import MalwareAlerts from './pages/MalwareAlerts'
import Whitelist from './pages/Whitelist'

const pages = [
  { key: 'dashboard', label: 'Dashboard', icon: FiGrid },
  { key: 'agents', label: 'Agents', icon: FiServer },
  { key: 'malware', label: 'Malware Alerts', icon: FiAlertTriangle },
  { key: 'whitelist', label: 'Whitelist Domains', icon: FiShield },
] as const

type PageKey = typeof pages[number]['key']

export default function App() {
  const [active, setActive] = useState<PageKey>('dashboard')
  const { colorMode, toggleColorMode } = useColorMode()
  const isDark = colorMode === 'dark'

  const sidebarBg = isDark ? 'gray.900' : 'white'
  const activeBg = isDark ? 'blue.600' : 'blue.50'
  const activeColor = isDark ? 'white' : 'blue.600'
  const textColor = isDark ? 'gray.400' : 'gray.500'

  const renderPage = () => {
    switch (active) {
      case 'dashboard': return <Dashboard />
      case 'agents': return <Agents />
      case 'malware': return <MalwareAlerts />
      case 'whitelist': return <Whitelist />
    }
  }

  return (
    <Flex h="100vh" overflow="hidden">
      {/* Sidebar */}
      <Box
        w="260px"
        bg={sidebarBg}
        borderRight="1px"
        borderColor={isDark ? 'gray.700' : 'gray.100'}
        py={6}
        px={4}
        display="flex"
        flexDirection="column"
      >
        {/* Logo */}
        <HStack spacing={3} px={3} mb={8}>
          <Flex w={10} h={10} borderRadius="xl" bg="blue.500" align="center" justify="center">
            <Text fontSize="xl" fontWeight="extrabold" color="white" letterSpacing="-1px">SX</Text>
          </Flex>
          <Box>
            <Text fontSize="lg" fontWeight="bold" lineHeight="1.2" color={isDark ? 'white' : 'gray.800'}>
              ShieldX
            </Text>
            <Text fontSize="xs" color="gray.400" fontWeight="medium">Agent Monitoring</Text>
          </Box>
        </HStack>

        {/* Navigation */}
        <VStack spacing={1} align="stretch" flex={1}>
          {pages.map(p => (
            <HStack
              key={p.key}
              as="button"
              onClick={() => setActive(p.key)}
              spacing={3}
              px={3}
              py={3}
              borderRadius="xl"
              bg={active === p.key ? activeBg : 'transparent'}
              color={active === p.key ? activeColor : textColor}
              fontWeight={active === p.key ? 'semibold' : 'medium'}
              fontSize="sm"
              _hover={{ bg: active === p.key ? activeBg : (isDark ? 'gray.800' : 'gray.50') }}
              transition="all 0.2s"
            >
              <Icon as={p.icon} w={5} h={5} />
              <Text>{p.label}</Text>
            </HStack>
          ))}
        </VStack>

        <Divider mb={4} borderColor={isDark ? 'gray.700' : 'gray.200'} />

        {/* Bottom controls */}
        <HStack justify="space-between" px={3}>
          <HStack spacing={2}>
            <Avatar size="sm" name="Admin" bg="blue.500">
              <AvatarBadge boxSize="1.25em" bg="green.400" />
            </Avatar>
            <Box>
              <Text fontSize="sm" fontWeight="medium" color={isDark ? 'white' : 'gray.700'}>Admin</Text>
              <Text fontSize="xs" color="gray.400">Online</Text>
            </Box>
          </HStack>
          <IconButton
            aria-label="Toggle theme"
            icon={isDark ? <FiSun /> : <FiMoon />}
            size="sm"
            variant="ghost"
            borderRadius="full"
            onClick={toggleColorMode}
          />
        </HStack>
      </Box>

      {/* Main Content */}
      <Box flex={1} overflowY="auto" bg={isDark ? 'gray.800' : 'gray.50'}>
        {renderPage()}
      </Box>
    </Flex>
  )
}
