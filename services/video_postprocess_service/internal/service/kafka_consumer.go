package service

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/IBM/sarama"
)

type MessageHandler func(message *sarama.ConsumerMessage) error

type KafkaConsumer struct {
	consumer    sarama.ConsumerGroup
	handler     MessageHandler
	workerCount int
	ready       chan bool
	messageChan chan *sarama.ConsumerMessage
	wg          sync.WaitGroup
	errors      chan error
}

func NewKafkaConsumer(brokers []string, groupID string, config *sarama.Config, workerCount int) (*KafkaConsumer, error) {
	consumer, err := sarama.NewConsumerGroup(brokers, groupID, config)
	if err != nil {
		return nil, fmt.Errorf("failed to create consumer group: %w", err)
	}

	return &KafkaConsumer{
		consumer:    consumer,
		workerCount: workerCount,
		ready:       make(chan bool),
		messageChan: make(chan *sarama.ConsumerMessage, workerCount*10),
		errors:      make(chan error, workerCount),
	}, nil
}

func (c *KafkaConsumer) SetHandler(handler MessageHandler) {
	c.handler = handler
}

func (c *KafkaConsumer) Errors() <-chan error {
	return c.errors
}

func (c *KafkaConsumer) Start(ctx context.Context, topics []string) error {
	if c.handler == nil {
		return errors.New("message handler must be set before starting")
	}

	for i := 0; i < c.workerCount; i++ {
		c.wg.Add(1)
		go c.worker(ctx)
	}

	c.wg.Add(1)
	go func() {
		defer c.wg.Done()
		for {
			select {
			case <-ctx.Done():
				return
			default:
				handler := &consumerGroupHandler{
					messageChan: c.messageChan,
					ready:       c.ready,
				}

				if err := c.consumer.Consume(ctx, topics, handler); err != nil {
					if errors.Is(err, sarama.ErrClosedConsumerGroup) {
						return
					}
					c.errors <- fmt.Errorf("consumer error: %w", err)
					time.Sleep(5 * time.Second)
				}
			}
		}
	}()

	<-c.ready
	log.Printf("Kafka consumer started with %d workers", c.workerCount)
	return nil
}

func (c *KafkaConsumer) worker(ctx context.Context) {
	defer c.wg.Done()

	for {
		select {
		case <-ctx.Done():
			return
		case msg, ok := <-c.messageChan:
			if !ok {
				return
			}

			if err := c.handler(msg); err != nil {
				c.errors <- fmt.Errorf("message processing failed: %w (topic: %s, partition: %d, offset: %d)",
					err, msg.Topic, msg.Partition, msg.Offset)
			}
		}
	}
}

func (c *KafkaConsumer) Close() error {
	close(c.messageChan)
	c.wg.Wait()
	close(c.errors)

	if err := c.consumer.Close(); err != nil {
		return fmt.Errorf("failed to close consumer: %w", err)
	}
	return nil
}

type consumerGroupHandler struct {
	messageChan chan<- *sarama.ConsumerMessage
	ready       chan<- bool
}

func (h *consumerGroupHandler) Setup(sarama.ConsumerGroupSession) error {
	close(h.ready)
	return nil
}

func (h *consumerGroupHandler) Cleanup(sarama.ConsumerGroupSession) error {
	return nil
}

func (h *consumerGroupHandler) ConsumeClaim(session sarama.ConsumerGroupSession, claim sarama.ConsumerGroupClaim) error {
	for message := range claim.Messages() {
		h.messageChan <- message
		session.MarkMessage(message, "")
	}
	return nil
}

func KafkaConsumerConfig(options ...func(*sarama.Config)) *sarama.Config {
	config := sarama.NewConfig()

	config.Version = sarama.V4_0_0_0
	config.ClientID = "video-processing-service"

	config.Consumer.Group.Rebalance.GroupStrategies = []sarama.BalanceStrategy{
		sarama.NewBalanceStrategySticky(),
	}
	config.Consumer.Group.Session.Timeout = 30 * time.Second
	config.Consumer.Group.Heartbeat.Interval = 10 * time.Second
	config.Consumer.Group.Rebalance.Timeout = 60 * time.Second

	config.Consumer.Return.Errors = true
	config.Consumer.Offsets.Initial = sarama.OffsetNewest
	config.Consumer.Offsets.AutoCommit.Enable = true
	config.Consumer.Offsets.AutoCommit.Interval = 5 * time.Second
	config.Consumer.Fetch.Min = 1
	config.Consumer.Fetch.Default = 1 * 1024 * 1024 // 1MB
	config.Consumer.MaxProcessingTime = 100 * time.Millisecond

	config.ChannelBufferSize = 256
	config.Net.MaxOpenRequests = 5

	config.Net.TLS.Enable = false
	config.Net.SASL.Enable = false

	for _, option := range options {
		option(config)
	}

	return config
}

func WithDebug() func(*sarama.Config) {
	return func(c *sarama.Config) {
		c.Consumer.Return.Errors = true
		c.Producer.Return.Successes = true
		c.Producer.Return.Errors = true
	}
}

func ParseJSONMessage(msg *sarama.ConsumerMessage, target interface{}) error {
	if err := json.Unmarshal(msg.Value, target); err != nil {
		return fmt.Errorf("failed to unmarshal message: %w (payload: %s)", err, string(msg.Value))
	}
	return nil
}
