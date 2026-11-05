import React from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchSuggestionsGraph } from '../services/connections';
import { ConnectionGraphView } from '../components/ConnectionGraphView';
import { EmptyState } from '../components/UIStates';

export const DiscoverGraph: React.FC = () => {
  const navigate = useNavigate();
  return (
    <ConnectionGraphView
      title="Discover"
      subtitle="People you could connect with next, based on your studies, your topics and your rooms."
      graphLabel="Graph of people you could connect with"
      listTitle="Best connections first"
      legend="The bigger and closer someone is, the more you have in common. A dashed ring means a friend request is pending."
      tone="learn"
      showStrength
      fetchGraph={fetchSuggestionsGraph}
      loadingMessage="Looking for connections..."
      renderEmpty={() => (
        <EmptyState
          title="No suggestions yet"
          description="Add your studies and the topics you want to learn, so we can find people to connect you with."
          actionLabel="Complete my profile"
          onAction={() => navigate('/my-profile')}
        />
      )}
    />
  );
};
